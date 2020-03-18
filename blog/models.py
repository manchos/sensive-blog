from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models import Count


class PostQuerySet(models.QuerySet):
    def year(self, year):
        posts_at_year = self.filter(published_at__year=year).order_by('published_at')
        return posts_at_year

    def popular(self, tag=None):
        if tag is not None:
            most_popular_posts = self.prefetch_related(
                'author').annotate(
                likes_count=Count('likes')).order_by('-likes_count').filter(
                tags__id__contains=tag.id)
        else:
            most_popular_posts = self.prefetch_related('author').annotate(
            likes_count=Count('likes')).order_by('-likes_count')
        return most_popular_posts

    def fetch_with_comments_count(self):
        most_popular_posts_ids = [post.id for post in self]
        posts_with_comments_list = []
        posts_with_comments = Post.objects.filter(
            id__in=most_popular_posts_ids).annotate(
            num_comments=Count('comments'))
        ids_and_comments = posts_with_comments.values_list('id', 'num_comments')
        count_for_id = dict(ids_and_comments)
        for post in self:
            post.num_comments = count_for_id[post.id]
            posts_with_comments_list.append(post)
        return posts_with_comments_list


class Post(models.Model):
    title = models.CharField("Заголовок", max_length=200)
    text = models.TextField("Текст")
    slug = models.SlugField("Название в виде url", max_length=200)
    image = models.ImageField("Картинка")
    published_at = models.DateTimeField("Дата и время публикации")

    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Автор", limit_choices_to={'is_staff': True})
    likes = models.ManyToManyField(User, related_name="liked_posts", verbose_name="Кто лайкнул", blank=True)
    tags = models.ManyToManyField("Tag", related_name="posts", verbose_name="Теги")

    objects = PostQuerySet.as_manager()

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args={'slug': self.slug})

    class Meta:
        ordering = ['-published_at']
        verbose_name = 'пост'
        verbose_name_plural = 'посты'


class TagQuerySet(models.QuerySet):
    def popular(self):
        populate_tags = self.annotate(
            num_posts=Count('posts', distinct=True)).order_by('-num_posts')

        return populate_tags


class Tag(models.Model):
    title = models.CharField("Тег", max_length=20, unique=True)

    def __str__(self):
        return self.title

    def clean(self):
        self.title = self.title.lower()

    def get_absolute_url(self):
        return reverse('tag_filter', args={'tag_title': self.slug})

    objects = TagQuerySet.as_manager()

    class Meta:
        ordering = ["title"]
        verbose_name = 'тег'
        verbose_name_plural = 'теги'


class Comment(models.Model):
    post = models.ForeignKey("Post",
                             on_delete=models.CASCADE,
                             verbose_name="Пост, к которому написан",
                             related_name="comments",
                             )
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               verbose_name="Автор",
                               related_name="comments",
                               )

    text = models.TextField("Текст комментария")
    published_at = models.DateTimeField("Дата и время публикации")

    def __str__(self):
        return f"{self.author.username} under {self.post.title}"

    class Meta:
        ordering = ['published_at']
        verbose_name = 'комментарий'
        verbose_name_plural = 'комментарии'
