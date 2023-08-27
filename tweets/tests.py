from django.test import TestCase
from django.urls import reverse

from accounts.models import User

from .models import Like, Tweet


class TestHomeView(TestCase):
    def setUp(self):
        self.url = reverse("tweets:home")
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")
        self.client.login(username="testuser", password="testpassword")

    def test_success_get(self):
        Tweet.objects.create(user=self.user, content="test tweet")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerysetEqual(response.context["tweet_list"], Tweet.objects.all())


class TestTweetCreateView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpassword")
        self.url = reverse("tweets:create")
        self.client.login(username="testuser", password="testpassword")

    def test_success_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_success_post(self):
        valid_data = {
            "content": "test content",
        }
        response = self.client.post(self.url, valid_data)

        self.assertRedirects(
            response,
            reverse("tweets:home"),
            status_code=302,
            target_status_code=200,
        )
        self.assertTrue(Tweet.objects.filter(**valid_data).exists())

    def test_failure_post_with_empty_content(self):
        invalid_data = {
            "content": "",
        }
        response = self.client.post(self.url, invalid_data)
        form = response.context["form"]

        self.assertEqual(response.status_code, 200)
        self.assertIn("このフィールドは必須です。", form.errors["content"])
        self.assertFalse(Tweet.objects.filter(**invalid_data).exists())

    def test_failure_post_with_too_long_content(self):
        invalid_data = {
            "content": "a" * 256,
        }
        response = self.client.post(self.url, invalid_data)
        form = response.context["form"]

        self.assertEqual(response.status_code, 200)
        self.assertIn(
            "この値は 255 文字以下でなければなりません( {} 文字になっています)。".format(len(invalid_data["content"])),
            form.errors["content"],
        )
        self.assertFalse(Tweet.objects.filter(**invalid_data).exists())


class TestTweetDetailView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="testuser", email="test@examle.com", password="testpassword")
        self.client.login(username="testuser", password="testpassword")
        self.tweet = Tweet.objects.create(user=self.user, content="test tweet")
        self.url = reverse("tweets:detail", kwargs={"pk": self.tweet.pk})

    def test_success_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["tweet"], self.tweet)


class TestTweetDeleteView(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="testuser1", email="test1@example.com", password="testpassword")
        self.user2 = User.objects.create_user(username="testuser2", email="test2@example.com", password="testpassword")
        self.client.login(
            username="testuser1",
            password="testpassword",
        )
        self.tweet1 = Tweet.objects.create(user=self.user1, content="tweet1")
        self.tweet2 = Tweet.objects.create(user=self.user2, content="tweet2")
        self.url1 = reverse("tweets:delete", kwargs={"pk": self.tweet1.pk})
        self.url2 = reverse("tweets:delete", kwargs={"pk": self.tweet2.pk})

    def test_success_post(self):
        response = self.client.post(self.url1)
        self.assertRedirects(response, reverse("tweets:home"), status_code=302, target_status_code=200)
        self.assertEqual(Tweet.objects.filter(content="tweet").count(), 0)

    def test_failure_post_with_not_exist_tweet(self):
        response = self.client.post(reverse("tweets:delete", kwargs={"pk": 99}))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Tweet.objects.count(), 2)

    def test_failure_post_with_incorrect_user(self):
        response = self.client.post(self.url2)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Tweet.objects.count(), 2)


class TestLikeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
        )
        self.client.login(username="testuser", password="testpassword")
        self.tweet = Tweet.objects.create(user=self.user, content="test_tweet")
        self.url = reverse("tweets:like", kwargs={"pk": self.tweet.pk})

    def test_success_post(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(tweet=self.tweet, user=self.user).exists())

    def test_failure_post_with_not_exist_tweet(self):
        url = reverse("tweets:like", kwargs={"pk": "100"})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Like.objects.filter(tweet=self.tweet, user=self.user).exists())

    def test_failure_post_with_liked_tweet(self):
        Like.objects.create(tweet=self.tweet, user=self.user)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Like.objects.filter(tweet=self.tweet, user=self.user).exists())


class TestUnLikeView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
        )
        self.client.login(username="testuser", password="testpassword")
        self.tweet = Tweet.objects.create(user=self.user, content="test_tweet")
        Like.objects.create(tweet=self.tweet, user=self.user)

    def test_success_post(self):
        response = self.client.post(reverse("tweets:unlike", kwargs={"pk": self.tweet.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(tweet=self.tweet, user=self.user).exists())

    def test_failure_post_with_not_exist_tweet(self):
        response = self.client.post(reverse("tweets:unlike", kwargs={"pk": 100}))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Like.objects.filter(tweet=self.tweet, user=self.user).exists())

    def test_failure_post_with_unliked_tweet(self):
        Like.objects.filter(tweet=self.tweet, user=self.user).delete()
        response = self.client.post(reverse("tweets:unlike", kwargs={"pk": self.tweet.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Like.objects.filter(tweet=self.tweet, user=self.user).exists())
