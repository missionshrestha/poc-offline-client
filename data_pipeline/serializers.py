# data_pipeline/serializers.py
from rest_framework import serializers


class PipelineRunRequestSerializer(serializers.Serializer):
    """
    Request shape for POST /api/pipelines/run/

    This is intentionally simple for the POC. Later you can extend it with:
      - pipeline configuration
      - dataset references
      - options flags, etc.
    """
    pipeline_id = serializers.CharField(max_length=100)
    parameters = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        help_text="Optional free-form parameters for the pipeline run.",
    )


class PipelineExportRequestSerializer(serializers.Serializer):
    """
    Request shape for POST /api/pipelines/export/
    """
    pipeline_id = serializers.CharField(max_length=100)
    export_format = serializers.ChoiceField(
        choices=["csv", "json", "parquet"],
        help_text="Export format (e.g. csv, json, parquet).",
    )
    options = serializers.DictField(
        child=serializers.JSONField(),
        required=False,
        help_text="Optional export options (compression, delimiter, etc.).",
    )


class CustomConnectorRequestSerializer(serializers.Serializer):
    """
    Request shape for POST /api/pipelines/custom-connector/

    This simulates invoking some custom, user-specific connector.
    """
    connector_key = serializers.CharField(
        max_length=100,
        help_text="Identifier for the custom connector to invoke.",
    )
    payload = serializers.DictField(
        child=serializers.JSONField(),
        help_text="Connector-specific payload (credentials, filters, etc.).",
    )
