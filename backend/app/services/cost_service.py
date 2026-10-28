from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.entities import Budget, Department, HiringRequest

TWO_PLACES = Decimal("0.01")
DAYS_IN_YEAR = Decimal("365")

# Currency conversion rates to base reporting currency (INR) using exact Decimal constants
FX_TO_INR: dict[str, Decimal] = {
    "INR": Decimal("1.00"),
    "USD": Decimal("84.00"),
    "EUR": Decimal("91.00"),
}


def quantize_money(value: Decimal) -> Decimal:
    return value.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


def calculate_request_annualized_forecast(
    *,
    est_annual_salary_per_pos: Decimal,
    est_benefits_cost_per_pos: Decimal,
    est_recruitment_fee_per_pos: Decimal,
    est_onetime_cost_per_pos: Decimal,
    headcount_requested: int,
) -> Decimal:
    """
    Calculates total first-year annualized forecast across all requested positions
    using strict Decimal arithmetic.
    """
    per_position = (
        Decimal(est_annual_salary_per_pos)
        + Decimal(est_benefits_cost_per_pos)
        + Decimal(est_recruitment_fee_per_pos)
        + Decimal(est_onetime_cost_per_pos)
    )
    return quantize_money(per_position * Decimal(headcount_requested))


def calculate_in_period_expenditure(
    *,
    est_annual_salary_per_pos: Decimal,
    est_benefits_cost_per_pos: Decimal,
    est_recruitment_fee_per_pos: Decimal,
    est_onetime_cost_per_pos: Decimal,
    headcount_requested: int,
    start_date: date,
    fiscal_year: int | None = None,
) -> Decimal:
    """
    Distinguishes annualized recurring compensation from actual in-period expenditure.
    Recurring salary + benefits are prorated by remaining active days in the fiscal year,
    while recruitment fees and one-time equipment/relocation costs are 100% recognized on hire.
    """
    fy = fiscal_year or settings.fiscal_year
    fy_start = date(fy, 1, 1)
    fy_end = date(fy, 12, 31)

    if start_date > fy_end:
        return Decimal("0.00")

    effective_start = max(start_date, fy_start)
    active_days = Decimal((fy_end - effective_start).days + 1)
    proration_factor = active_days / DAYS_IN_YEAR

    recurring_per_pos = (
        Decimal(est_annual_salary_per_pos) + Decimal(est_benefits_cost_per_pos)
    ) * proration_factor
    onetime_per_pos = Decimal(est_recruitment_fee_per_pos) + Decimal(est_onetime_cost_per_pos)
    total = (recurring_per_pos + onetime_per_pos) * Decimal(headcount_requested)
    return quantize_money(total)


def calculate_cost_of_delayed_hiring(
    *,
    est_annual_salary_per_pos: Decimal,
    open_positions_count: int,
    delay_days: int,
    productivity_multiplier: Decimal = Decimal("1.35"),
) -> dict[str, Decimal]:
    """
    Estimates the business impact of delayed hiring versus payroll savings during vacancy.
    """
    if delay_days <= 0 or open_positions_count <= 0:
        return {
            "vacancy_payroll_savings": Decimal("0.00"),
            "estimated_productivity_loss": Decimal("0.00"),
            "net_delay_cost": Decimal("0.00"),
        }
    daily_salary = Decimal(est_annual_salary_per_pos) / DAYS_IN_YEAR
    days = Decimal(delay_days)
    positions = Decimal(open_positions_count)

    payroll_savings = quantize_money(daily_salary * days * positions)
    productivity_loss = quantize_money(daily_salary * productivity_multiplier * days * positions)
    net_cost = quantize_money(productivity_loss - payroll_savings)
    return {
        "vacancy_payroll_savings": payroll_savings,
        "estimated_productivity_loss": productivity_loss,
        "net_delay_cost": net_cost,
    }


def compute_workforce_and_cost_summary(
    db: Session,
    *,
    department_id: str | None = None,
    business_unit: str | None = None,
    job_grade: str | None = None,
    country: str | None = None,
) -> dict:
    """
    Aggregates workforce headcount and financial metrics at the Position and Request grains
    without double-counting across approval stages.
    """
    stmt = select(HiringRequest)
    if department_id:
        stmt = stmt.where(HiringRequest.department_id == department_id)
    if business_unit:
        stmt = stmt.where(HiringRequest.business_unit == business_unit)
    if job_grade:
        stmt = stmt.where(HiringRequest.job_grade == job_grade)
    if country:
        stmt = stmt.where(HiringRequest.country == country)

    requests = list(db.scalars(stmt).unique().all())

    requested_headcount = 0
    approved_headcount = 0
    open_approved_positions = 0
    filled_positions = 0

    annualized_base_salary = Decimal("0.00")
    annualized_benefits = Decimal("0.00")
    recruitment_and_onetime = Decimal("0.00")
    forecast_total_cost = Decimal("0.00")
    in_period_forecast_cost = Decimal("0.00")
    actual_total_cost = Decimal("0.00")

    approved_statuses = {"APPROVED", "RECRUITING", "PARTIALLY_FILLED", "FILLED", "CLOSED"}

    for req in requests:
        fx = FX_TO_INR.get(req.currency, Decimal("1.00"))
        if req.status != "CANCELLED":
            requested_headcount += req.headcount_requested

        if req.status in approved_statuses:
            # Count each position once based on its current status
            for pos in req.positions:
                if pos.status in {"APPROVED", "OPEN_RECRUITING", "FILLED"}:
                    approved_headcount += 1
                    annualized_base_salary += Decimal(req.est_annual_salary_per_pos) * fx
                    annualized_benefits += Decimal(req.est_benefits_cost_per_pos) * fx
                    recruitment_and_onetime += (
                        Decimal(req.est_recruitment_fee_per_pos) + Decimal(req.est_onetime_cost_per_pos)
                    ) * fx
                if pos.status in {"APPROVED", "OPEN_RECRUITING"}:
                    open_approved_positions += 1
                if pos.status == "FILLED":
                    filled_positions += 1
                    if pos.outcome and pos.outcome.closure_status == "HIRED":
                        out = pos.outcome
                        actual_total_cost += (
                            Decimal(out.actual_annual_base_salary)
                            + Decimal(out.actual_benefits_cost)
                            + Decimal(out.actual_recruitment_fee)
                            + Decimal(out.actual_onetime_cost)
                        ) * fx

            forecast_total_cost += Decimal(req.total_annualized_forecast) * fx
            in_period_forecast_cost += (
                calculate_in_period_expenditure(
                    est_annual_salary_per_pos=req.est_annual_salary_per_pos,
                    est_benefits_cost_per_pos=req.est_benefits_cost_per_pos,
                    est_recruitment_fee_per_pos=req.est_recruitment_fee_per_pos,
                    est_onetime_cost_per_pos=req.est_onetime_cost_per_pos,
                    headcount_requested=req.headcount_requested,
                    start_date=req.requested_start_date,
                )
                * fx
            )

    # Budget rollup
    budget_stmt = select(Budget).join(Department, Budget.department_id == Department.id)
    if department_id:
        budget_stmt = budget_stmt.where(Budget.department_id == department_id)
    if business_unit:
        budget_stmt = budget_stmt.where(Department.business_unit == business_unit)

    budgets = list(db.scalars(budget_stmt).all())
    total_allocated_budget = sum(
        (Decimal(b.allocated_budget) * FX_TO_INR.get(b.currency, Decimal("1.00")) for b in budgets),
        Decimal("0.00"),
    )
    budget_variance = quantize_money(total_allocated_budget - forecast_total_cost)
    utilization_pct = (
        quantize_money((forecast_total_cost / total_allocated_budget) * Decimal("100"))
        if total_allocated_budget > Decimal("0.00")
        else Decimal("0.00")
    )

    return {
        "reporting_currency": "INR",
        "requested_headcount": requested_headcount,
        "approved_headcount": approved_headcount,
        "open_approved_positions": open_approved_positions,
        "filled_positions": filled_positions,
        "annualized_base_salary_commitment": quantize_money(annualized_base_salary),
        "employer_benefits_commitment": quantize_money(annualized_benefits),
        "recruitment_and_onetime_costs": quantize_money(recruitment_and_onetime),
        "forecast_total_hiring_cost": quantize_money(forecast_total_cost),
        "in_period_projected_expenditure": quantize_money(in_period_forecast_cost),
        "actual_total_hiring_cost": quantize_money(actual_total_cost),
        "actual_vs_approved_variance": quantize_money(actual_total_cost - forecast_total_cost),
        "allocated_department_budget": quantize_money(total_allocated_budget),
        "budget_utilization_pct": utilization_pct,
        "budget_variance": budget_variance,
    }
