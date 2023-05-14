import inspect
from abc import abstractmethod
from typing import Type, Optional, Callable, List, Tuple, Union

import pytest
from bs4 import BeautifulSoup
from bs4.element import SoupStrainer
from django.db.models import Model
from django.http import HttpResponse
from django.test.client import Client
from mixer.main import Mixer

from adapters.model_adapter import ModelAdapter
from adapters.post import PostModelAdapter
from conftest import N_PER_PAGE, UrlRepr, _testget_context_item_by_class

pytestmark = [
    pytest.mark.django_db
]


class ContentTester:
    n_per_page = N_PER_PAGE

    def __init__(self,
                 mixer: Mixer,
                 item_cls: Type[Model],
                 adapter_cls: Type[ModelAdapter],
                 user_client: Client,
                 page_url: Optional[UrlRepr] = None,
                 another_user_client: Optional[Client] = None,
                 unlogged_client: Optional[Client] = None
                 ):
        self._mixer = mixer
        self._items_key = None
        self._page_url = page_url
        self.item_cls = item_cls
        self.adapter_cls = adapter_cls
        self.user_client = user_client
        self.another_user_client = another_user_client
        self.unlogged_client = unlogged_client

    @property
    def page_url(self):
        return self._page_url

    @property
    @abstractmethod
    def which_obj(self):
        ...

    @property
    @abstractmethod
    def which_objs(self):
        ...

    @property
    @abstractmethod
    def one_and_only_one(self):
        ...

    @property
    @abstractmethod
    def at_least_one(self):
        ...

    @property
    @abstractmethod
    def of_which_obj(self):
        ...

    @property
    @abstractmethod
    def which_page(self):
        ...

    @property
    @abstractmethod
    def on_which_page(self):
        ...

    @property
    @abstractmethod
    def to_which_page(self):
        ...

    @property
    @abstractmethod
    def of_which_page(self):
        ...

    def raise_assert_page_loads_cbk(self):
        raise AssertionError(
            f'Убедитесь, что {self.which_page} загружается без ошибок.')

    def user_client_testget(
            self, url: Optional[str] = None,
            assert_status_in: Tuple[int] = (200,),
            assert_cbk: Union[Callable[[], None], str] = (
                    'raise_assert_page_loads_cbk')
    ) -> HttpResponse:

        url = url or self.page_url.url
        try:
            response = self.user_client.get(url)
            if response.status_code not in assert_status_in:
                raise Exception
        except Exception:
            if inspect.isfunction(assert_cbk):
                assert_cbk()
            elif isinstance(assert_cbk, str):
                getattr(self, assert_cbk)()
            else:
                raise AssertionError('Wrong type of `assert_cbk` argument.')

        return response

    @property
    def items_key(self):
        if self._items_key:
            return self._items_key

        def setup_for_url(setup_items: List[Model]) -> UrlRepr:
            temp_category = self._mixer.blend('blog.Category',
                                              is_published=True)
            temp_location = self._mixer.blend('blog.Location',
                                              is_published=True)
            temp_post = self._mixer.blend(
                'blog.Post', is_published=True,
                location=temp_location,
                category=temp_category)
            setup_items.extend([temp_category, temp_location, temp_post])
            url_repr = UrlRepr(
                f'/category/{temp_category.slug}/',
                '/category/<category_slug>/')
            return url_repr

        def teardown(setup_items: List[Model]):
            while setup_items:
                item = setup_items.pop()
                item.delete()

        setup_items = []

        key_missing_msg = (
            f'Убедитесь, что в словарь контекста {self.of_which_page} '
            f'передаются {self.which_objs}.'
        )
        try:
            url_repr = setup_for_url(setup_items)
            key_val = _testget_context_item_by_class(
                self.user_client_testget(url=url_repr.url).context,
                self.item_cls,
                err_msg=key_missing_msg, inside_iter=True
            )
        finally:
            teardown(setup_items)

        return key_val.key

    def n_or_page_size(self, n: int):
        return min(self.n_per_page, n)


class PostContentTester(ContentTester):

    @property
    def which_obj(self):
        return 'публикация'

    @property
    def which_objs(self):
        return 'публикации'

    @property
    def one_and_only_one(self):
        return 'одна и только одна'

    @property
    def at_least_one(self):
        return 'хотя бы одна'

    @property
    def of_which_obj(self):
        return 'публикации'

    @property
    def of_which_objs(self):
        return 'публикаций'


class ProfilePostContentTester(PostContentTester):

    @property
    def which_page(self):
        return 'страница пользователя'

    @property
    def on_which_page(self):
        return 'на странице пользователя'

    @property
    def to_which_page(self):
        return 'на страницу пользователя'

    @property
    def of_which_page(self):
        return 'страницы пользователя'


class MainPostContentTester(PostContentTester):

    @property
    def which_page(self):
        return 'главная страница'

    @property
    def on_which_page(self):
        return 'на главной странице'

    @property
    def to_which_page(self):
        return 'на главную страницу'

    @property
    def of_which_page(self):
        return 'главной страницы'


class CategoryPostContentTester(PostContentTester):

    @property
    def page_url(self):
        if not self._page_url:
            from blog.models import Category
            category = Category.objects.first()
            if category:
                self._page_url = UrlRepr(
                    f'/category/{category.slug}/',
                    '/category/<category_slug>/')
        return self._page_url

    @property
    def which_page(self):
        return 'страница категории'

    @property
    def on_which_page(self):
        return 'на странице категории'

    @property
    def to_which_page(self):
        return 'на страницу категории'

    @property
    def of_which_page(self):
        return 'страницы категории'


@pytest.fixture
def profile_content_tester(
        user: Model, mixer: Mixer, PostModel: Type[Model], user_client: Client,
        another_user_client: Client, unlogged_client: Client
) -> ProfilePostContentTester:
    url_repr = UrlRepr(f'/profile/{user.username}/', '/profile/<username>/')
    return ProfilePostContentTester(
        mixer, PostModel, PostModelAdapter, user_client, url_repr)


@pytest.fixture
def main_content_tester(
        user: Model, mixer: Mixer, PostModel: Type[Model], user_client: Client,
        another_user_client: Client, unlogged_client: Client
) -> MainPostContentTester:
    url_repr = UrlRepr('/', '/')
    return MainPostContentTester(
        mixer, PostModel, PostModelAdapter, user_client, url_repr)


@pytest.fixture
def category_content_tester(
        user: Model, mixer: Mixer, PostModel: Type[Model], user_client: Client,
        another_user_client: Client, unlogged_client: Client
) -> CategoryPostContentTester:
    return CategoryPostContentTester(
        mixer, PostModel, PostModelAdapter, user_client)


class TestContent:

    @pytest.fixture(autouse=True)
    def init(self, profile_content_tester, main_content_tester,
             category_content_tester):
        self.profile_tester = profile_content_tester
        self.main_tester = main_content_tester
        self.category_tester = category_content_tester

    def test_unpublished(
            self, unpublished_posts_with_published_locations):
        profile_response = self.profile_tester.user_client_testget()
        context_posts = profile_response.context.get(
            self.profile_tester.items_key)
        expected_n = self.profile_tester.n_or_page_size(
            len(unpublished_posts_with_published_locations))
        assert len(context_posts) == expected_n, (
            f'Убедитесь, что {self.profile_tester.on_which_page} '
            'авторизованному пользователю отображаются '
            f'{self.profile_tester.which_objs}, снятые с публикации.'
        )

        for tester in (self.main_tester, self.category_tester):
            response = tester.user_client_testget()
            context_posts = response.context.get(tester.items_key)
            assert len(context_posts) == 0, (
                f'Убедитесь, что {tester.on_which_page} не отображаются '
                f'{tester.which_objs}, снятые с публикации.'
            )

    def test_unpublished_category(
            self, user_client, posts_with_unpublished_category
    ):
        profile_response = self.profile_tester.user_client_testget()
        context_posts = profile_response.context.get(
            self.profile_tester.items_key)
        expected_n = self.profile_tester.n_or_page_size(
            len(posts_with_unpublished_category))
        assert len(context_posts) == expected_n, (
            f'Убедитесь, что {self.profile_tester.on_which_page} '
            'авторизованному пользователю отображаются '
            f'{self.profile_tester.which_objs} категории, снятой с публикации.'
        )

        main_response = self.main_tester.user_client_testget()
        context_posts = main_response.context.get(self.main_tester.items_key)
        assert len(context_posts) == 0, (
            f'Убедитесь, что {self.main_tester.on_which_page} не отображаются '
            f'{self.main_tester.which_objs} категории снятой с публикации.'
        )

        def raise_assert_not_exist_cbk():
            raise AssertionError(
                f'Убедитесь, что {self.category_tester.which_page} '
                f'не существует, если категория не опубликована.')

        self.category_tester.user_client_testget(
            assert_status_in=(404,),
            assert_cbk=raise_assert_not_exist_cbk
        )

    def test_future_posts(self, user_client, future_posts):
        profile_response = self.profile_tester.user_client_testget()
        context_posts = profile_response.context.get(
            self.profile_tester.items_key)
        expected_n = self.profile_tester.n_or_page_size(len(future_posts))
        assert len(context_posts) == expected_n, (
            f'Убедитесь, что {self.profile_tester.on_which_page} '
            'авторизованному пользователю отображаются отложенные '
            f'{self.profile_tester.which_objs}.')

        for tester in (self.main_tester, self.category_tester):
            response = tester.user_client_testget()
            context_posts = response.context.get(tester.items_key)
            assert len(context_posts) == 0, (
                f'Убедитесь, что {tester.on_which_page} не отображаются '
                f'отложенные {tester.which_objs}.')

    def test_pagination(self, user_client,
                        many_posts_with_published_locations):
        posts = many_posts_with_published_locations

        assert len(posts) > self.profile_tester.n_per_page
        assert len(posts) > self.main_tester.n_per_page
        assert len(posts) > self.category_tester.n_per_page

        for tester in (
                self.profile_tester, self.main_tester, self.category_tester):
            response = tester.user_client_testget()
            context_posts = response.context.get(tester.items_key)
            expected_n = tester.n_or_page_size(len(posts))
            assert len(context_posts) == expected_n, (
                f'Убедитесь, что {tester.on_which_page} работает пагинация.')

    def test_image_visible(self, user_client, post_with_published_location):
        post = post_with_published_location
        post_adapter = PostModelAdapter(post)

        img_n_with_post_img = {}
        for tester in (
                self.profile_tester, self.main_tester, self.category_tester):
            img_soup_with_post_img = BeautifulSoup(
                tester.user_client_testget().content.decode('utf-8'),
                features='html.parser',
                parse_only=SoupStrainer('img'))
            img_n_with_post_img[tester.on_which_page] = len(
                img_soup_with_post_img)

        post_adapter.image = None
        post_adapter.save()

        for tester in (
                self.profile_tester, self.main_tester, self.category_tester):
            img_soup_without_post_img = BeautifulSoup(
                tester.user_client_testget().content.decode('utf-8'),
                features='html.parser',
                parse_only=SoupStrainer('img'))
            img_n_without_post_img = len(img_soup_without_post_img)
            assert (img_n_with_post_img[tester.on_which_page]
                    - img_n_without_post_img) == 1, (
                f'Убедитесь, что {tester.on_which_page} отображаются '
                f'изображения {tester.of_which_objs}.'
            )
