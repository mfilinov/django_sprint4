from abc import abstractmethod
from typing import Set, Tuple, Optional

from django.db.models import QuerySet, Model
from django.http import HttpResponse

from form.base_form_tester import (
    UnauthorizedSubmitTester, AnonymousSubmitTester,
    AuthorisedSubmitTester, SubmitTester)
from form.base_tester import BaseTester


class DeleteTester(BaseTester):

    @property
    def of_which_action(self):
        return 'удаления'

    @property
    def of_which_query(self):
        return f'запроса на удаление {self.of_which_obj}'

    @property
    @abstractmethod
    def redirect_to_page(self):
        ...

    def redirect_error_message(self, by_user: str, redirect_to_page: str):
        return (
            f'Убедитесь, что при отправке {self.of_which_query} '
            f'{self.on_which_page} {by_user} '
            f'он перенаправляется на {redirect_to_page}.'
        )

    def status_error_message(self, by_user: str):
        return (
            f'Убедитесь, что при отправке {self.of_which_query} '
            f'{self.of_which_obj} {by_user} не возникает ошибок.')

    def test_delete_item(self, qs: QuerySet,
                         delete_url_addr: str) -> HttpResponse:
        instances_before: Set[Model] = set(qs.all())

        can_delete, response = self.user_can_delete(
            UnauthorizedSubmitTester(
                tester=self,
                test_response_cbk=(
                    UnauthorizedSubmitTester.get_test_response_redirect_cbk(
                        tester=self,
                        redirect_to_page=self.redirect_to_page
                    ))),
            delete_url_addr, self._item_adapter, qs=qs)
        assert not can_delete, (
            f'Убедитесь, что {self.which_obj} не может быть удалена '
            'неавторизованным пользователем.')

        can_delete, response = self.user_can_delete(
            AnonymousSubmitTester(
                tester=self,
                test_response_cbk=(
                    AnonymousSubmitTester.get_test_response_redirect_cbk(
                        tester=self,
                        redirect_to_page=self.redirect_to_page
                    ))),
            delete_url_addr, self._item_adapter, qs=qs)
        assert not can_delete, (
            f'Убедитесь, что {self.which_obj} не может быть удалена '
            'неаутентифицированным пользователем.')

        can_delete, response = self.user_can_delete(
            AuthorisedSubmitTester(
                tester=self,
                test_response_cbk=(
                    AuthorisedSubmitTester.get_test_response_ok_cbk(
                        tester=self
                    ))),
            delete_url_addr, self._item_adapter, qs=qs)
        assert can_delete, (
            f'Убедитесь, что при отправке {self.of_which_query} '
            f'{self.on_which_page} {self.which_obj} не отображается '
            'на странице ответа.')

        instances_after: Set[Model] = set(qs.all())

        deleted_instances_n = instances_before - instances_after
        assert len(deleted_instances_n) == 1, (
            f'Убедитесь, что при отправке {self.of_which_query} '
            f'{self.on_which_page} {self.which_obj} удаляется из базы данных.')

        AuthorisedSubmitTester(
            tester=self,
            test_response_cbk=AuthorisedSubmitTester.get_test_response_404_cbk(
                tester=self)
        ).test_submit(url=delete_url_addr, data={})

        return response

    def user_can_delete(
            self, submitter: SubmitTester, delete_url, item_to_delete_adapter,
            qs: QuerySet
    ) -> Tuple[Optional[bool], Optional[HttpResponse]]:
        response = submitter.test_submit(url=delete_url, data={})
        deleted = qs.filter(id=item_to_delete_adapter.id).first() is None
        return deleted, response
