from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow
from .utils import make_paginator


@cache_page(20, key_prefix='index_page')
def index(request):
    """Возравращает 10 постов на главной странице."""
    posts = Post.objects.all()

    context = {
        'page_obj': make_paginator(request, posts),
    }

    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Возравращает 10 постов конкретной группы."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()

    context = {
        'group': group,
        'page_obj': make_paginator(request, posts),
    }

    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Будет отображаться информация об авторе и его посты.
    В following проверяем подписан ли текущий пользователь на автора,
    страницу которого он просматривает.
    """
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    following = (request.user.is_authenticated and author.following.filter(
        user=request.user).exists())

    context = {
        'author': author,
        'page_obj': make_paginator(request, posts),
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница для просмотра отдельного поста."""
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {'post': post, 'comments': comments, 'form': form,
               }

    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Страница для создания поста."""
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == "POST":
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()

            return redirect('posts:profile', request.user)

    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Страница для редактирования поста."""
    post = get_object_or_404(Post, pk=post_id)
    is_edit = True
    if post.author != request.user:

        return redirect('posts:post_detail', post_id)

    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if request.method == 'POST':
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()

            return redirect('posts:post_detail', post_id)

    return render(request, 'posts/create_post.html',
                  {'post': post, 'form': form, 'is_edit': is_edit})


@login_required
def add_comment(request, post_id):
    """Добавляем комменатрий."""
    post = get_object_or_404(Post.objects.select_related(), id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с постами авторов, на которых подписан текущий пользователь.
    Информация о текущем пользователе доступна в переменной request.user.
    Following - ссылка на объект пользователя, на которого подписываются.
    """
    followed_posts = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': make_paginator(request, followed_posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Страница для подписки на автора с редиректом на профайл."""
    following_author = get_object_or_404(User, username=username)
    if (
        Follow.objects.filter(author=following_author,
                              user=request.user).exists()
        or request.user == following_author
    ):
        return redirect('posts:profile', username=username)

    Follow.objects.create(
        user=request.user,
        author=following_author,
    )

    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Страница для отписки от автора с редиректом на профайл."""
    author_to_unfollow = get_object_or_404(User, username=username)
    follower = Follow.objects.filter(user=request.user,
                                     author=author_to_unfollow)
    if follower.exists():
        follower.delete()
    return redirect('posts:profile', username=username)
