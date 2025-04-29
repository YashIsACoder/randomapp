from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import FoodEntry
from datetime import date, timedelta
from sqlalchemy import func
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Home page: show today’s entries and weekly calorie chart."""
    today = date.today()

    # 1. Fetch entries and compute today’s total in one query
    entries = (
        FoodEntry.query
        .filter_by(user_id=current_user.id, date=today)
        .order_by(FoodEntry.time)
        .all()
    )
    total_calories = sum(e.calories for e in entries)

    # 2. Get user’s target (default 2000)
    target = getattr(current_user.profile, 'target_calories', 2000)

    # 3. Weekly aggregation via SQL (push work into DB)
    week_start = today - timedelta(days=today.weekday())
    weekly = (
        FoodEntry.query
        .with_entities(
            func.date(FoodEntry.date).label('day'),
            func.sum(FoodEntry.calories).label('cal_sum')
        )
        .filter(
            FoodEntry.user_id == current_user.id,
            FoodEntry.date.between(week_start, today)
        )
        .group_by('day')
        .order_by('day')
        .all()
    )

    # 4. Unpack for chart
    dates = [row.day.isoformat() for row in weekly]
    calories = [row.cal_sum for row in weekly]

    logger.debug("Index data prepared", extra={
        "user": current_user.id,
        "today_total": total_calories,
        "weekly_points": len(weekly)
    })

    return render_template(
        'main/index.html',
        title='Home',
        today_entries=entries,
        total_calories=total_calories,
        target_calories=target,
        dates=dates,
        calories=calories,
    )

@bp.route('/about')
def about():
    """About page."""
    return render_template('main/about.html', title='About')
