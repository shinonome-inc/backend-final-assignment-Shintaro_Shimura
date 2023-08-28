from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, View

from .forms import TweetCreateForm
from .models import Like, Tweet


class HomeView(LoginRequiredMixin, ListView):
    template_name = "tweets/home.html"
    model = Tweet

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tweet_list"] = Tweet.objects.select_related("user").prefetch_related("liked_tweet")
        liked_list = (
            Like.objects.filter(user=self.request.user).select_related("tweet").values_list("tweet_id", flat=True)
        )
        context["liked_list"] = liked_list
        return context


class TweetCreateView(LoginRequiredMixin, CreateView):
    template_name = "tweets/create.html"
    form_class = TweetCreateForm
    success_url = reverse_lazy("tweets:home")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class TweetDetailView(LoginRequiredMixin, DetailView):
    template_name = "tweets/detail.html"
    model = Tweet
    queryset = model.objects.select_related("user").prefetch_related("liked_tweet")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        liked_list = (
            Like.objects.select_related("tweet").filter(user=self.request.user).values_list("tweet_id", flat=True)
        )
        context["liked_list"] = liked_list
        return context


class TweetDeleteView(UserPassesTestMixin, DeleteView):
    template_name = "tweets/delete.html"
    model = Tweet
    success_url = reverse_lazy("tweets:home")

    def test_func(self):
        return self.request.user == self.get_object().user


class LikeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tweet_id = self.kwargs["pk"]
        tweet = get_object_or_404(Tweet, id=tweet_id)
        Like.objects.get_or_create(tweet=tweet, user=self.request.user)
        unlike_url = reverse("tweets:unlike", kwargs={"pk": tweet_id})
        tweet = Tweet.objects.prefetch_related("liked_tweet").get(id=tweet_id)
        like_count = tweet.liked_tweet.count()
        is_liked = True
        context = {
            "like_count": like_count,
            "tweet_id": tweet_id,
            "is_liked": is_liked,
            "unlike_url": unlike_url,
        }
        return JsonResponse(context)


class UnlikeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        tweet_id = self.kwargs["pk"]
        tweet = get_object_or_404(Tweet, pk=tweet_id)
        if like := Like.objects.filter(user=self.request.user, tweet=tweet):
            like.delete()
        is_liked = False
        like_url = reverse("tweets:like", kwargs={"pk": tweet_id})
        tweet = Tweet.objects.prefetch_related("liked_tweet").get(id=tweet_id)
        like_count = tweet.liked_tweet.count()
        context = {
            "like_count": like_count,
            "tweet_id": tweet_id,
            "is_liked": is_liked,
            "like_url": like_url,
        }
        return JsonResponse(context)
