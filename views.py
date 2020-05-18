import calendar

from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from drf_yasg.utils import swagger_auto_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from apps.auth.permissions import HasModelPermissions
from apps.core.services.drf import base_response, BaseResponseAutoSchema, get_swagger_responses
from apps.reports.financial import services
from apps.reports.financial.models import FinancialReport
from apps.reports.financial.serializers import FinancialReportRequestSerializer, CreateFinancialReportCampaignSerializer, \
    FinancialReportResponseSerializer, UpdateFinancialReportCampaignSerializer
from apps.reports.financial.services import create_financial_report, update_financial_report


class FinancialReportViewSet(ViewSet):
    permission_classes = (HasModelPermissions,)
    permission_model = FinancialReport

    @swagger_auto_schema(query_serializer=FinancialReportRequestSerializer, responses=get_swagger_responses(FinancialReportResponseSerializer(many=True)),
                         auto_schema=BaseResponseAutoSchema, operation_summary=_('Get Financial Report'), operation_description=_('Returns a financial report.'))
    def list(self, request: Request) -> Response:
        request_serializer = FinancialReportRequestSerializer(data=request.query_params)
        request_serializer.is_valid(raise_exception=True)
        validated_data = request_serializer.validated_data
        report = services.get_report(user=request.user, interval_from=request_serializer.data.get('interval_from'), interval_to=request_serializer.data.get('interval_to'),
                                     advertiser_ids=validated_data.get('advertiser_id'), campaign_ids=validated_data.get('campaign_id'), status=validated_data.get('status'),
                                     category_id=validated_data.get('category_id'))
        response_serializer = FinancialReportResponseSerializer(data=report, many=True)
        response_serializer.is_valid()
        return base_response(response_serializer.data)

    @swagger_auto_schema(request_body=CreateFinancialReportCampaignSerializer, responses=get_swagger_responses(FinancialReportResponseSerializer),
                         auto_schema=BaseResponseAutoSchema, operation_summary=_('Create Financial Report'), operation_description=_('Returns a created financial report record.'))
    def create(self, request: Request) -> Response:
        request_serializer = CreateFinancialReportCampaignSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        instance = create_financial_report(**request_serializer.validated_data)
        report_date = request_serializer.validated_data['report_date']
        interval_from = str(report_date)
        week_day, last_day = calendar.monthrange(report_date.year, report_date.month)
        interval_to = f'{report_date.year}-{report_date.month}-{last_day}'
        report = services.get_report(user=request.user, interval_from=interval_from, interval_to=interval_to, campaign_ids=[instance.campaign_id])
        response_serializer = FinancialReportResponseSerializer(data=report, many=True)
        response_serializer.is_valid()
        return base_response(response_serializer.data)

    @swagger_auto_schema(query_serializer=UpdateFinancialReportCampaignSerializer, responses=get_swagger_responses(FinancialReportResponseSerializer),
                         auto_schema=BaseResponseAutoSchema, operation_summary=_('Update Financial Report'), operation_description=_('Returns an updated financial report record.'))
    def partial_update(self, request: Request, pk: int) -> Response:
        request_serializer = UpdateFinancialReportCampaignSerializer(data=request.data)
        request_serializer.is_valid(raise_exception=True)
        instance = get_object_or_404(FinancialReport.active.all(), id=pk)
        instance = update_financial_report(instance, **request_serializer.validated_data)
        report_date = instance.report_date
        interval_from = str(report_date)
        week_day, last_day = calendar.monthrange(report_date.year, report_date.month)
        interval_to = f'{report_date.year}-{report_date.month}-{last_day}'
        report = services.get_report(user=request.user, interval_from=interval_from, interval_to=interval_to, campaign_ids=[instance.campaign.id])
        response_serializer = FinancialReportResponseSerializer(data=report, many=True)
        response_serializer.is_valid()
        return base_response(response_serializer.data)
