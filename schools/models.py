from django.db import models

class School(models.Model):
    name = models.CharField(max_length=200)
    code = models.SlugField(unique=True)
    def __str__(self):
        return self.code

class Student(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="students")
    school_student_id = models.CharField(max_length=64)
    full_name = models.CharField(max_length=200, blank=True)
    class Meta:
        unique_together = ("school", "school_student_id")

class StudentIdMap(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name="student_id_maps")
    # provider dimension not required if provider_student_id is unique per school
    provider_student_id = models.CharField(max_length=128)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="provider_ids")
    class Meta:
        unique_together = ("school", "provider_student_id")

class SchoolDirectoryConnection(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="directory")
    base_url = models.URLField()
    api_key = models.TextField()
    timeout_seconds = models.IntegerField(default=10)
    # Directory resolves canonical student by provider_student_id alone
    student_by_provider_id_path = models.CharField(max_length=200, default="/students/by-provider-id/{provider_student_id}")


class QBOConnection(models.Model):
    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="qbo")
    realm_id = models.CharField(max_length=32)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expires_at = models.DateTimeField()
    company_currency = models.CharField(max_length=3, default="USD")