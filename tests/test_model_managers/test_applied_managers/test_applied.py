from app.utils import DateGen, minute_before_now, now, timed_tomorrow

from .fixtures import *

now_ = DateGen(now())


def test_entry_manager_return_all_expenses(entry_manager):
    num_expenses = len(expenses)
    manager_expenses = entry_manager.today(now_).ext.expenses()
    assert all(
        isinstance(obj, entry_manager.model) for obj in manager_expenses
    )
    assert manager_expenses.count() == num_expenses


def test_entry_manager_return_all_income(entry_manager):
    num_income = len(income)
    manager_income = entry_manager.today(now_).ext.income()
    assert all(isinstance(obj, entry_manager.model) for obj in manager_income)
    assert manager_income.count() == num_income


def test_entry_manager_filter_expenses_by_budget_id(entry_manager):
    first_budget_num = len(
        [item for item in expenses if item["budget_id"] == 1]
    )
    second_budget_num = len(
        [item for item in expenses if item["budget_id"] == 2]
    )
    manager_expenses = entry_manager.today(
        now_, filters=["budget_id==1"]
    ).ext.expenses()
    assert manager_expenses.count() == first_budget_num
    manager_expenses = entry_manager.today(
        now_, filters=["budget_id==2"]
    ).ext.expenses()
    assert manager_expenses.count() == second_budget_num


def test_entry_manager_filter_income_by_budget_id(entry_manager):
    first_budget_num = len([item for item in income if item["budget_id"] == 1])
    second_budget_num = len(
        [item for item in income if item["budget_id"] == 2]
    )
    manager_income = entry_manager.today(
        now_, filters=["budget_id==1"]
    ).ext.income()
    assert manager_income.count() == first_budget_num
    manager_income = entry_manager.today(
        now_, filters=["budget_id==2"]
    ).ext.income()
    assert manager_income.count() == second_budget_num


def test_entry_manager_filter_expenses_by_category_id(entry_manager):
    first_category_len = len(
        [item for item in expenses if item["category_id"] == 1]
    )
    second_category_len = len(
        [item for item in expenses if item["category_id"] == 2]
    )
    third_category_len = len(
        [item for item in expenses if item["category_id"] == 3]
    )
    manager_expenses = entry_manager.today(
        now_, filters=["category_id==1"]
    ).ext.expenses()
    assert manager_expenses.count() == first_category_len
    manager_expenses = entry_manager.today(
        now_, filters=["category_id==2"]
    ).ext.expenses()
    assert manager_expenses.count() == second_category_len
    manager_expenses = entry_manager.today(
        now_, filters=["category_id==3"]
    ).ext.expenses()
    assert manager_expenses.count() == third_category_len


def test_entry_manager_filter_income_by_category_id(entry_manager):
    first_category_len = len(
        [item for item in income if item["category_id"] == 1]
    )
    second_category_len = len(
        [item for item in income if item["category_id"] == 2]
    )
    manager_income = entry_manager.today(
        now_, filters=["category_id==1"]
    ).ext.income()
    assert manager_income.count() == first_category_len
    manager_income = entry_manager.today(
        now_, filters=["category_id==2"]
    ).ext.income()
    assert manager_income.count() == second_category_len


def test_entry_manager_sort_query_by_transaction_date(
    db_session, entry_manager
):
    later = {
        "id": 999,
        "budget_id": 1,
        "category_id": 3,
        "sum": -200,
        "transaction_date": timed_tomorrow(),
    }
    latest = {
        "id": 9999,
        "budget_id": 1,
        "category_id": 3,
        "sum": -10000,
        "transaction_date": timed_tomorrow(),
    }

    db_session.add_all([models.Entry(**later), models.Entry(**latest)])
    db_session.commit()

    expenses_ = entry_manager.this_year(now_).ext.expenses().all()
    assert expenses_[-1].id == latest["id"]
    assert expenses_[-2].id == later["id"]


def test_entry_manager_reverse_sort_query_by_transaction_date(
    db_session, entry_manager
):
    later = {
        "id": 999,
        "budget_id": 1,
        "category_id": 3,
        "sum": -200,
        "transaction_date": timed_tomorrow(),
    }
    latest = {
        "id": 9999,
        "budget_id": 1,
        "category_id": 3,
        "sum": -10000,
        "transaction_date": timed_tomorrow(),
    }

    db_session.add_all([models.Entry(**later), models.Entry(**latest)])
    db_session.commit()

    expenses_ = (
        entry_manager.this_year(now_, reverse=True).ext.expenses().all()
    )
    assert expenses_[0].id == latest["id"]
    assert expenses_[1].id == later["id"]


def test_entry_manager_calculate_expenses_sum_correctly(entry_manager):
    expected_sum = sum(item["sum"] for item in expenses)
    manager_sum = entry_manager.today(now_).ext.expenses().sum()
    assert manager_sum == expected_sum


def test_entry_manager_calculate_income_sum_correctly(entry_manager):
    expected_sum = sum(item["sum"] for item in income)
    manager_sum = entry_manager.today(now_).ext.income().sum()
    assert manager_sum == expected_sum


def test_entry_manager_calculate_total_sum_correctly(entry_manager):
    expected_sum = sum(item["sum"] for item in income + expenses)
    manager_sum = entry_manager.today(now_).ext.total_sum()
    assert manager_sum == expected_sum


def test_entry_manager_sum_return_zero_if_no_entries_found(entry_manager):
    faulty_filter = ["budget_id==9999"]
    assert (
        entry_manager.today(now_, filters=faulty_filter).ext.total_sum() == 0
    )
