from django.shortcuts import render
from blog.models import Comment, Post, Tag
from django.db.models import Count

MOST_POPULAR_POSTS_COUNT = 5
MOST_FRESH_POSTS_COUNT = 5
LETTERS_COUNT = 200
TAGS_COUNT = 5

def get_related_posts_count(tag):
    return tag.posts.count()


def get_most_popular_posts(
        posts=Post.objects.prefetch_related('author'),
        num_posts=5):
    return posts.order_by('-num_likes')[:num_posts]


def get_most_popular_tags(num_tags=5):
    return Tag.objects.annotate(
        num_posts=Count('posts')).order_by('-num_posts')[:num_tags]


def serialize_post(post):
    return {
        "title": post.title,
        "teaser_text": post.text[:LETTERS_COUNT],
        "author": post.author.username,
        "comments_amount": len(Comment.objects.filter(post=post)),
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def serialize_post_optimized(post):
    return {
        "title": post.title,
        "teaser_text": post.text[:LETTERS_COUNT],
        "author": post.author.username,
        "comments_amount": post.num_comments,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
        'first_tag_title': post.tags.all()[0].title,
    }


def get_most_popular_posts_optimized(posts_count=None, tagid=None):

    if tagid is not None:
        most_popular_posts = Post.objects.prefetch_related('author').annotate(
            likes_count=Count('likes')).order_by('-likes_count').filter(tags__id__contains=tagid)[:posts_count]
    else:
        most_popular_posts = Post.objects.prefetch_related('author').annotate(
            likes_count=Count('likes')).order_by('-likes_count')[:posts_count]

    most_popular_posts_ids = [post.id for post in most_popular_posts]
    posts_with_comments = Post.objects.filter(
        id__in=most_popular_posts_ids).annotate(
        num_comments=Count('comments'))
    ids_and_comments = posts_with_comments.values_list('id', 'num_comments')
    count_for_id = dict(ids_and_comments)
    for post in most_popular_posts:
        post.num_comments = count_for_id[post.id]

    return most_popular_posts


def serialize_tag(tag):
    return {
        'title': tag.title,
        # 'posts_with_tag': Post.objects.filter(tags=tag).count(),
        'posts_with_tag': tag.num_posts if hasattr(tag, 'num_posts') else Post.objects.filter(tags=tag).count(),
    }


def index(request):
    most_popular_posts = Post.objects.popular().fetch_with_comments_count()[:5]
    most_fresh_posts = Post.objects \
                           .prefetch_related('author').order_by('-published_at') \
                           .fetch_with_comments_count()[:5]
    most_popular_tags = Tag.objects.popular()[:TAGS_COUNT]

    context = {
        'most_popular_posts': [serialize_post_optimized(post) for post in most_popular_posts],
        'page_posts': [serialize_post_optimized(post) for post in most_fresh_posts],
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
    }
    return render(request, 'index.html', context)


def post_detail(request, slug):
    post = Post.objects.select_related('author').prefetch_related('tags') \
        .prefetch_related('comments').annotate(likes_count=Count('likes')) \
        .get(slug=slug)

    serialized_comments = []

    for comment in post.comments.all():
        serialized_comments.append({
            'text': comment.text,
            'published_at': comment.published_at,
            'author': comment.author.username,
        })

    serialized_post = {
        "title": post.title,
        "text": post.text,
        "author": post.author.username,
        "comments": serialized_comments,
        'likes_amount': post.likes_count,
        "image_url": post.image.url if post.image else None,
        "published_at": post.published_at,
        "slug": post.slug,
        "tags": [serialize_tag(tag) for tag in post.tags.all()],
    }

    most_popular_tags = Tag.objects.popular()[:TAGS_COUNT]

    most_popular_posts = get_most_popular_posts_optimized(MOST_POPULAR_POSTS_COUNT)

    context = {
        'post': serialized_post,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        'most_popular_posts': [serialize_post_optimized(post) for post in most_popular_posts],
    }
    return render(request, 'post-details.html', context)


def tag_filter(request, tag_title):
    tag = Tag.objects.get(title=tag_title)

    most_popular_tags = Tag.objects.popular()[:TAGS_COUNT]

    most_popular_posts = get_most_popular_posts_optimized(MOST_POPULAR_POSTS_COUNT)

    related_posts = get_most_popular_posts_optimized(20, tag.id)

    context = {
        "tag": tag.title,
        'popular_tags': [serialize_tag(tag) for tag in most_popular_tags],
        "posts": [serialize_post_optimized(post) for post in related_posts],
        'most_popular_posts': [serialize_post_optimized(post) for post in most_popular_posts],
    }
    return render(request, 'posts-list.html', context)


def contacts(request):
    # позже здесь будет код для статистики заходов на эту страницу
    # и для записи фидбека
    return render(request, 'contacts.html', {})
