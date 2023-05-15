from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, \
    DeleteView
from django.utils import timezone
from blog.models import Post, Category

User = get_user_model()


class PostMixin:
    model = Post
    fields = '__all__'
    template_name = 'blog/create.html'


class PostCreateView(CreateView, PostMixin):
    success_url = reverse_lazy('blog:index')


class PostUpdateView(UpdateView, PostMixin):
    success_url = reverse_lazy('blog:index')


class PostDeleteView(DeleteView, PostMixin):
    success_url = reverse_lazy('blog:index')


class IndexListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return (
            self.model.objects.select_related('location', 'author', 'category')
            .filter(is_published=True,
                    category__is_published=True,
                    pub_date__lte=timezone.now()))


class ProfileListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/profile.html'

    def get_queryset(self):
        return (
            self.model.objects.select_related('author')
            .filter(author__username=self.kwargs['username']))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username'])
        return context


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'

    def get_object(self, queryset=None):
        return get_object_or_404(
            self.model.objects.select_related('location', 'author', 'category')
            .filter(pub_date__lte=timezone.now(),
                    is_published=True,
                    category__is_published=True), pk=self.kwargs['id'])


class CategoryPostsListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/category.html'

    # def get_queryset(self):
    #     return (
    #         self.model.objects.select_related('location', 'author', 'category')
    #         .filter(is_published=True,
    #                 category__is_published=True,
    #                 pub_date__lte=timezone.now(),
    #                 category_id=self.kwargs['category_slug']))
    #
    # def get_context_data(self, **kwargs):
    #     context = super().get_context_data(**kwargs)
    #     context['category'] = get_object_or_404(
    #         Category.objects.values('id', 'title', 'description'),
    #         slug=self.kwargs['category_slug'])
    #     return context


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.values('id', 'title', 'description')
        .filter(is_published=True, slug=category_slug))
    post_list = (
        Post.objects.select_related('location', 'author', 'category')
        .filter(is_published=True,
                category__is_published=True,
                pub_date__lte=timezone.now(),
                category_id=category['id']))
    context = {'category': category,
               'page_obj': post_list}
    return render(request, template, context)
