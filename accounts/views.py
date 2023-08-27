from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View

from tweets.models import Like, Tweet

from .forms import SignupForm
from .models import FriendShip, User


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy(settings.LOGIN_REDIRECT_URL)

    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data["username"]
        password = form.cleaned_data["password1"]
        user = authenticate(self.request, username=username, password=password)
        login(self.request, user)
        return response


class UserProfileView(LoginRequiredMixin, DetailView):
    model = User
    context_object_name = "user"
    template_name = "accounts/profile.html"
    slug_field = "username"
    slug_url_kwarg = "username"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        tweets = Tweet.objects.select_related("user").prefetch_related("liked_tweet").filter(user=user)
        context["tweet_user"] = user
        context["tweet_list"] = tweets.order_by("-created_at")
        context["is_following"] = FriendShip.objects.filter(following=user, follower=self.request.user).exists()
        context["following_num"] = FriendShip.objects.filter(follower=user).count()
        context["followers_num"] = FriendShip.objects.filter(following=user).count()
        liked_list = Like.objects.filter(user=self.request.user).values_list("tweet_id", flat=True)
        context["liked_list"] = liked_list
        return context


class FollowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        following = get_object_or_404(User, username=self.kwargs["username"])
        follower = request.user

        if following == follower:
            return HttpResponseBadRequest("自分自身はフォローできません。")

        if FriendShip.objects.filter(following=following, follower=follower).exists():
            messages.warning(request, "フォロー済です。")
            return redirect("tweets:home")

        FriendShip.objects.create(following=following, follower=follower)
        messages.success(request, "フォローしました")
        return redirect("tweets:home")


class UnFollowView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        following = get_object_or_404(User, username=self.kwargs["username"])
        follower = request.user

        if following == follower:
            return HttpResponseBadRequest("自分自身を対象には出来ません。")

        FriendShip.objects.filter(following=following, follower=follower).delete()
        messages.success(request, "フォローを外しました")
        return redirect("tweets:home")


class FollowerListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "accounts/follower_list.html"
    context_object_name = "follower_friendships"

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return FriendShip.objects.select_related("follower").filter(following=user)


class FollowingListView(LoginRequiredMixin, ListView):
    model = User
    template_name = "accounts/following_list.html"
    context_object_name = "following_friendships"

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs["username"])
        return FriendShip.objects.select_related("following").filter(follower=user)
