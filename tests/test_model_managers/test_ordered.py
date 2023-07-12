from sqlalchemy.orm import Query

from app.utils import timed_tomorrow, timed_yesterday

from .fixtures import (
    BaseTestModel,
    create_tables,
    db_session,
    engine,
    ordered_manager,
    populate_db,
)


def test_flow_create_ordered_manager_without_session(db_session):
    from app.db.managers import OrderedQueryManager

    mgr = OrderedQueryManager(BaseTestModel, order_by=["created_at", "id"])
    assert isinstance(mgr, OrderedQueryManager)
    assert mgr.model is BaseTestModel
    assert mgr.session is None

    # associate session with manager
    mgr(db_session)

    assert mgr.session is not None
    assert isinstance(mgr.all(), Query)


def test_order_by_property_return_joined_string_of_properties(ordered_manager):
    order_by = ["created_at", "id", "last_updated"]
    ordered_manager._order_by = order_by
    assert ordered_manager.order_by == ", ".join(order_by)


def test_inverse_order_by_property_add_desc_suffix_to_all_order_items(
    ordered_manager,
):
    order_by = ["created_at", "id", "last_updated"]
    ordered_manager._order_by = order_by
    expected = [item + " desc" for item in order_by]
    assert ordered_manager.inverse_order_by == ", ".join(expected)


def test_inverse_order_by_property_remove_desc_suffix_to_all_order_items(
    ordered_manager,
):
    order_by = ["created_at desc", "id desc", "last_updated desc"]
    ordered_manager._order_by = order_by
    expected = [item.removesuffix(" desc") for item in order_by]
    assert ordered_manager.inverse_order_by == ", ".join(expected)


def test_inverse_order_by_property_remove_and_add_desc_suffix_where_needed(
    ordered_manager,
):
    order_by = ["created_at desc", "id desc", "last_updated"]
    ordered_manager._order_by = order_by
    expected = ["created_at", "id", "last_updated desc"]
    assert ordered_manager.inverse_order_by == ", ".join(expected)


def test_all_method_return_ordered_query(ordered_manager):
    objects = ordered_manager.all()
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] < dates[i + 1] for i in range(len(dates) - 1)])


def test_all_method_with_reverse_arg_return_query_in_descending_order(
    ordered_manager,
):
    objects = ordered_manager.all(reverse=True)
    dates = [obj.created_at for obj in objects.all()]
    assert all([dates[i] > dates[i + 1] for i in range(len(dates) - 1)])


def test_list_method_return_ordered_query(ordered_manager):
    objects = ordered_manager.list()
    dates = [obj.created_at for obj in objects]
    assert all([dates[i] < dates[i + 1] for i in range(len(dates) - 1)])


def test_list_method_with_reverse_arg_return_query_in_descending_order(
    ordered_manager,
):
    objects = ordered_manager.list(reverse=True)
    dates = [obj.created_at for obj in objects]
    assert all([dates[i] > dates[i + 1] for i in range(len(dates) - 1)])


def test_first_method_return_first_added_instance(db_session, ordered_manager):
    db_session.add(BaseTestModel(name="new_obj", created_at=timed_yesterday()))
    db_session.commit()

    first_from_db = ordered_manager.first()
    assert isinstance(first_from_db, BaseTestModel)
    assert first_from_db.name == "new_obj"


def test_last_method_return_last_added_instance(db_session, ordered_manager):
    db_session.add(BaseTestModel(name="new_obj", created_at=timed_tomorrow()))
    db_session.commit()

    last_from_db = ordered_manager.last()
    assert isinstance(last_from_db, BaseTestModel)
    assert last_from_db.name == "new_obj"


def test_first_n_return_given_number_of_first_added_instances(
    db_session, ordered_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            BaseTestModel(name=test_name, created_at=timed_yesterday())
            for test_name in test_names
        ]
    )
    db_session.commit()

    first_n_from_db = ordered_manager.first_n(sample_size)
    assert isinstance(first_n_from_db, Query)

    first_n_from_db = first_n_from_db.all()
    assert len(first_n_from_db) == sample_size

    first_n_names = [obj.name for obj in first_n_from_db]
    assert first_n_names == test_names


def test_first_n_return_empty_result_for_zero_arg(ordered_manager):
    first_n_from_db = ordered_manager.first_n(0)
    assert isinstance(first_n_from_db, Query)
    assert first_n_from_db.all() == []


def test_last_n_return_given_number_of_last_added_instances(
    db_session, ordered_manager
):
    sample_size = 5
    test_names = [f"new_obj{i}" for i in range(sample_size)]

    db_session.add_all(
        [
            BaseTestModel(name=test_name, created_at=timed_tomorrow())
            for test_name in test_names
        ]
    )
    db_session.commit()

    last_n_from_db = ordered_manager.last_n(sample_size)
    assert isinstance(last_n_from_db, Query)

    last_n_from_db = last_n_from_db.all()
    assert len(last_n_from_db) == sample_size

    last_n_names = [obj.name for obj in last_n_from_db]
    assert last_n_names == list(reversed(test_names))


def test_last_n_return_empty_result_for_zero_arg(ordered_manager):
    last_n_from_db = ordered_manager.last_n(0)
    assert isinstance(last_n_from_db, Query)
    assert last_n_from_db.all() == []
