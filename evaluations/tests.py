from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from evaluations.models import Evaluation, Appeal
from courses.models import Course, CourseOffering, Enrollment

User = get_user_model()


class EvaluationsBaseMixin:
    """Base mixin for evaluation tests with common setup"""
    
    def setUp(self):
        # Create users
        self.student = User.objects.create_user(
            username='student1',
            password='pass123',
            role='student'
        )
        self.professor = User.objects.create_user(
            username='prof1',
            password='pass123',
            role='professor'
        )
        self.admin = User.objects.create_user(
            username='admin1',
            password='pass123',
            role='admin'
        )
        
        # Create course and offering
        self.course = Course.objects.create(
            code='CS101',
            title='Intro to CS',
            description='Introduction to Computer Science'
        )
        self.offering = CourseOffering.objects.create(
            course=self.course,
            professor=self.professor,
            term='1405-1',
            capacity=30,
            is_active=True
        )
        
        # Enroll student
        self.enrollment = Enrollment.objects.create(
            student=self.student,
            offering=self.offering,
            status='active'
        )


class EvaluationModelTests(EvaluationsBaseMixin, TestCase):
    """Tests for Evaluation model"""
    
    def test_unique_evaluation_per_student_per_offering(self):
        """Test that a student can only evaluate an offering once"""
        Evaluation.objects.create(
            student=self.student,
            offering=self.offering,
            rating=4,
            comment='Good course'
        )
        
        # Try to create duplicate - should raise IntegrityError
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Evaluation.objects.create(
                student=self.student,
                offering=self.offering,
                rating=5,
                comment='Another evaluation'
            )
    
    def test_appeal_lock_if_decided(self):
        """Test that appeal cannot be modified after decision"""
        evaluation = Evaluation.objects.create(
            student=self.student,
            offering=self.offering,
            rating=2,
            comment='Poor course'
        )
        
        appeal = Appeal.objects.create(
            evaluation=evaluation,
            reason='Unfair rating'
        )
        
        # Accept the appeal
        appeal.status = 'accepted'
        appeal.decided_at = timezone.now()
        appeal.save()
        
        # Verify lock_if_decided returns True
        self.assertTrue(appeal.lock_if_decided())
        self.assertEqual(appeal.status, 'accepted')
        self.assertIsNotNone(appeal.decided_at)


class EvaluateProfessorViewTests(EvaluationsBaseMixin, TestCase):
    """Tests for evaluate_professor view"""
    
    def test_login_required(self):
        """Test that login is required to evaluate"""
        url = reverse('evaluations:evaluate_professor', args=[self.offering.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
    
    def test_non_enrolled_student_cannot_evaluate(self):
        """Test that non-enrolled students cannot evaluate"""
        # Create non-enrolled student
        non_enrolled = User.objects.create_user(
            username='student2',
            password='pass123',
            role='student'
        )
        self.client.login(username='student2', password='pass123')
        
        url = reverse('evaluations:evaluate_professor', args=[self.offering.id])
        resp = self.client.post(url, {
            'rating': 4,
            'comment': 'Good'
        })
        
        self.assertEqual(resp.status_code, 403)
    
    def test_enrolled_student_can_evaluate(self):
        """Test that enrolled student can submit evaluation"""
        self.client.login(username='student1', password='pass123')
        
        url = reverse('evaluations:evaluate_professor', args=[self.offering.id])
        resp = self.client.post(url, {
            'rating': 4,
            'comment': 'Great course!'
        })
        
        self.assertRedirects(resp, reverse('core:dashboard'))
        
        # Verify evaluation was created
        evaluation = Evaluation.objects.get(
            student=self.student,
            offering=self.offering
        )
        self.assertEqual(evaluation.rating, 4)
        self.assertEqual(evaluation.comment, 'Great course!')
    
    def test_duplicate_evaluation_prevented(self):
        """Test that student cannot evaluate twice"""
        # Create first evaluation
        Evaluation.objects.create(
            student=self.student,
            offering=self.offering,
            rating=4,
            comment='First evaluation'
        )
        
        self.client.login(username='student1', password='pass123')
        
        url = reverse('evaluations:evaluate_professor', args=[self.offering.id])
        resp = self.client.post(url, {
            'rating': 5,
            'comment': 'Second evaluation'
        })
        
        self.assertEqual(resp.status_code, 403)
        
        # Verify only one evaluation exists
        count = Evaluation.objects.filter(
            student=self.student,
            offering=self.offering
        ).count()
        self.assertEqual(count, 1)


class AppealEvaluationViewTests(EvaluationsBaseMixin, TestCase):
    """Tests for appeal_evaluation view"""
    
    def setUp(self):
        super().setUp()
        # Create an evaluation to appeal
        self.evaluation = Evaluation.objects.create(
            student=self.student,
            offering=self.offering,
            rating=2,
            comment='Poor course'
        )
    
    def test_login_required(self):
        """Test that login is required to appeal"""
        url = reverse('evaluations:appeal_evaluation', args=[self.evaluation.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login/', resp.url)
    
    def test_only_professor_can_appeal_their_evaluation(self):
        """Test that only the professor of the course can appeal"""
        # Create another professor
        other_prof = User.objects.create_user(
            username='prof2',
            password='pass123',
            role='professor'
        )
        self.client.login(username='prof2', password='pass123')
        
        url = reverse('evaluations:appeal_evaluation', args=[self.evaluation.id])
        resp = self.client.post(url, {
            'reason': 'Unfair rating'
        })
        
        self.assertEqual(resp.status_code, 403)
    
    def test_professor_can_appeal_evaluation(self):
        """Test that professor can submit appeal"""
        self.client.login(username='prof1', password='pass123')
        
        url = reverse('evaluations:appeal_evaluation', args=[self.evaluation.id])
        resp = self.client.post(url, {
            'reason': 'This rating is unfair'
        })
        
        self.assertRedirects(resp, reverse('core:dashboard'))
        
        # Verify appeal was created
        appeal = Appeal.objects.get(evaluation=self.evaluation)
        self.assertEqual(appeal.reason, 'This rating is unfair')
        self.assertEqual(appeal.status, 'pending')
    
    def test_duplicate_appeal_prevented(self):
        """Test that professor cannot appeal twice"""
        # Create first appeal
        Appeal.objects.create(
            evaluation=self.evaluation,
            reason='First appeal'
        )
        
        self.client.login(username='prof1', password='pass123')
        
        url = reverse('evaluations:appeal_evaluation', args=[self.evaluation.id])
        resp = self.client.post(url, {
            'reason': 'Second appeal'
        })
        
        self.assertEqual(resp.status_code, 403)
        
        # Verify only one appeal exists
        count = Appeal.objects.filter(evaluation=self.evaluation).count()
        self.assertEqual(count, 1)


class AdminAppealsViewsTests(EvaluationsBaseMixin, TestCase):
    """Tests for admin appeals management views"""
    
    def setUp(self):
        super().setUp()
        # Create evaluation and appeal
        self.evaluation = Evaluation.objects.create(
            student=self.student,
            offering=self.offering,
            rating=2,
            comment='Poor course'
        )
        self.appeal = Appeal.objects.create(
            evaluation=self.evaluation,
            reason='Unfair rating'
        )
    
    def test_admin_appeals_list_requires_admin(self):
        """Test that only admin can access appeals list"""
        # Try as student
        self.client.login(username='student1', password='pass123')
        url = reverse('evaluations:admin_appeals_list')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
        
        # Try as professor
        self.client.login(username='prof1', password='pass123')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 403)
    
    def test_admin_can_access_appeals_list(self):
        """Test that admin can view appeals list"""
        self.client.login(username='admin1', password='pass123')
        url = reverse('evaluations:admin_appeals_list')
        resp = self.client.get(url)
        
        self.assertEqual(resp.status_code, 200)
        self.assertIn(self.appeal, resp.context['appeals'])
    
    def test_update_appeal_status_requires_admin(self):
        """Test that only admin can update appeal status"""
        self.client.login(username='prof1', password='pass123')
        url = reverse('evaluations:update_appeal_status', args=[self.appeal.id])
        resp = self.client.post(url, {'status': 'accepted'})
        
        self.assertEqual(resp.status_code, 403)
    
    def test_update_appeal_status_requires_post(self):
        """Test that update requires POST method"""
        self.client.login(username='admin1', password='pass123')
        url = reverse('evaluations:update_appeal_status', args=[self.appeal.id])
        resp = self.client.get(url)
        
        self.assertEqual(resp.status_code, 405)
    
    def test_admin_can_accept_appeal(self):
        """Test that admin can accept an appeal"""
        self.client.login(username='admin1', password='pass123')
        url = reverse('evaluations:update_appeal_status', args=[self.appeal.id])
        
        resp = self.client.post(url, {'status': 'accepted'})
        
        self.assertRedirects(resp, reverse('evaluations:admin_appeals_list'))
        
        # Verify appeal was updated
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, 'accepted')
        self.assertIsNotNone(self.appeal.decided_at)
    
    def test_cannot_update_decided_appeal(self):
        """Test that decided appeals cannot be modified"""
        # Mark appeal as decided
        self.appeal.status = 'accepted'
        self.appeal.decided_at = timezone.now()
        self.appeal.save()
        
        self.client.login(username='admin1', password='pass123')
        url = reverse('evaluations:update_appeal_status', args=[self.appeal.id])
        
        resp = self.client.post(url, {'status': 'rejected'})
        
        self.assertEqual(resp.status_code, 403)
        
        # Verify appeal was not changed
        self.appeal.refresh_from_db()
        self.assertEqual(self.appeal.status, 'accepted')

