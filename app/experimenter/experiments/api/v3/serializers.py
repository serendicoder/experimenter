from django.utils.text import slugify
from rest_framework import serializers

from experimenter.bugzilla.tasks import create_experiment_bug_task
from experimenter.experiments.models import Experiment
from experimenter.experiments.changelog_utils import ChangelogSerializerMixin


class ExperimentRapidSerializer(ChangelogSerializerMixin, serializers.ModelSerializer):
    type = serializers.HiddenField(default=Experiment.TYPE_RAPID)
    rapid_type = serializers.HiddenField(default=Experiment.RAPID_AA_CFR)
    owner = serializers.ReadOnlyField(source="owner.email")
    slug = serializers.ReadOnlyField()
    public_description = serializers.HiddenField(
        default=Experiment.BUGZILLA_RAPID_EXPERIMENT_TEMPLATE
    )
    objectives = serializers.CharField(required=True)

    class Meta:
        model = Experiment
        fields = (
            "type",
            "rapid_type",
            "owner",
            "name",
            "slug",
            "objectives",
            "public_description",
            "features",
            "audience",
        )

    def create(self, validated_data):
        validated_data.update(
            {
                "slug": slugify(validated_data["name"]),
                "owner": self.context["request"].user,
            }
        )
        experiment = super().create(validated_data)
        self.update_changelog(experiment, validated_data)
        create_experiment_bug_task.delay(experiment.owner.id, experiment.id)
        return experiment

    def update(self, instance, validated_data):
        updated_instance = super().update(instance, validated_data)
        self.update_changelog(updated_instance, validated_data)
        return updated_instance
