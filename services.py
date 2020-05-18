import calendar

from typing import Dict, Optional
from django.db.models import QuerySet, F
from django.conf import settings
from apps.auth.services import get_advertisers
from apps.core.models import CampaignStatus
from apps.core.services.databases import get_ch_connection
from apps.core.services.campaigns import get_campaigns, get_campaign_launch_number
from apps.reports.financial.models import FinancialReport
from apps.reports.financial.serializers import UpdateFinancialReportCampaignSerializer
from config.settings import AUTH_USER_MODEL


def get_common_data(campaign_ids: list, interval_from: str, interval_to: str) -> Dict:
    ch = get_ch_connection()
    data = {}
    query = f"""
            SELECT campaign_id,
                   sum(lead) AS leads_sum,
                   sum(bad_lead) AS bad_leads_sum,
                   count() AS general_count,
                   round(bad_leads_sum / general_count * 100, 2) AS bad_leads_percent
            FROM calls_stat
            WHERE  event_date BETWEEN '{interval_from}' AND '{interval_to}'
                 AND campaign_id IN ({','.join(map(str, campaign_ids))})
            GROUP BY campaign_id
        """
    rows = ch.execute(query)

    for row in rows:
        data[row[0]] = {'leads_sum': row[1], 'bad_leads_percent': row[2]}

    return data


def get_financial_report(campaign_ids: list, interval_from: str, interval_to: str) -> Dict:
    data = {}

    # Checking if the dates are within one month and the first and last day of the month is specified
    interval_from_year, interval_from_month, interval_from_day = [int(el) for el in interval_from.split('-')]
    interval_to_year, interval_to_month, interval_to_day = [int(el) for el in interval_to.split('-')]
    if interval_from_month == interval_to_month:
        week_day, month_last_day = calendar.monthrange(int(interval_from_year), int(interval_from_month))
        if interval_to_day == month_last_day:
            reports = FinancialReport.active.filter(campaign_id__in=campaign_ids, report_date__range=(interval_from, interval_to)).select_related('campaign').annotate(
                    plan=F('campaign__monthly_call_transfer_limit')).values('id', 'campaign_id', 'lead_cost', 'increased_plan', 'accepted_by_customer', 'plan', 'reviewed',
                                                                            'upd_number', 'account_number', 'account_date', 'additional_agreement', 'comment')
            for report in reports:
                data[report['campaign_id']] = report
                data[report['campaign_id']]['forecast'] = int(round(report['plan'] * 0.9, 2)),  # We estimate 90% of plan
    return data


def get_campaign_report(campaigns: QuerySet, common_data: Dict, reports_data: Dict) -> Dict:
    data = {}

    for campaign in campaigns:
        campaign_status = campaign.status_history.filter(status=CampaignStatus.launched.value).first()
        fact = common_data[campaign.id]['leads_sum']
        campaign_data = {
            'campaign': {
                'id': campaign.id,
                'status': campaign.status,
            },
            'report': {},
            'indicators': {
                'fact': fact,
                'launch_number': get_campaign_launch_number(campaign),
                'date_launched': campaign_status.date_created,
                'defect_percent': common_data[campaign.id]['bad_leads_percent']
            }
        }

        if reports_data.get(campaign.id):
            campaign_data['report'] = reports_data[campaign.id]
            campaign_data['indicators']['fact_in_money'] = fact * campaign_data['report']['lead_cost']
            campaign_data['indicators']['plan_in_money'] = campaign_data['report']['plan'] * campaign_data['report']['lead_cost']
            campaign_data['indicators']['increased_plan_in_money'] = campaign_data['report']['increased_plan'] * campaign_data['report']['lead_cost']
            campaign_data['indicators']['real_fact'] = fact if fact < campaign_data['report']['plan'] else fact
            campaign_data['indicators']['real_fact_percent'] = round(fact / campaign_data['report']['plan'] * 100, 2) if fact < campaign_data['report']['plan'] else 100.0
            campaign_data['indicators']['accepted_by_customer_percent'] = round(campaign_data['report']['accepted_by_customer'] / fact * 100, 2)

        if campaign.advertiser.id not in data:
            data[campaign.advertiser.id] = []
        data[campaign.advertiser.id].append(campaign_data)
    return data


def get_report(user: AUTH_USER_MODEL, interval_from: str, interval_to: str, advertiser_ids: Optional[list] = None, campaign_ids: Optional[list] = None,
               status: Optional[list] = None, category_id: Optional[int] = None):
    data = []
    status = [CampaignStatus.launched.value, CampaignStatus.paused.value] if status is None else [status]
    category = [category_id for category_id in settings.CAMPAIGN_CATEGORIES.keys()] if category_id is None else [category_id]

    if campaign_ids:
        campaigns = get_campaigns({'id': campaign_ids, 'status': status, 'category': category}, user)
    else:
        advertisers = get_advertisers({'id': advertiser_ids}) if advertiser_ids else get_advertisers()
        campaigns = get_campaigns({'advertiser_id': list(advertisers.values_list('id', flat=True)), 'status': status, 'category': category}, user)
        campaign_ids = list(campaigns.values_list('id', flat=True))

    if campaigns:
        common_data = get_common_data(campaign_ids, interval_from, interval_to)
        reports_data = get_financial_report(campaign_ids, interval_from, interval_to)
        campaigns_data = get_campaign_report(campaigns, common_data, reports_data)

        for key, value in campaigns_data.items():
            data.append({'advertiser_id': key, 'campaigns': value})
    return data


def create_financial_report(**kwargs) -> FinancialReport:
    return FinancialReport.objects.create(**kwargs)


def update_financial_report(instance: FinancialReport, **kwargs) -> FinancialReport:
    update_fields = []
    for field in UpdateFinancialReportCampaignSerializer.Meta.fields:
        if kwargs.get(field):
            setattr(instance, field, kwargs[field])
            update_fields.append(field)
    if update_fields:
        instance.save(update_fields=update_fields)
    return instance
