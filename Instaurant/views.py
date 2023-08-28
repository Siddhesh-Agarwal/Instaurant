from django.conf import settings
from django.http import (
    HttpRequest,
    HttpResponse,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
)
from django.shortcuts import render, redirect
from .models import Contact, Post, BlogComment, Series
from django.contrib import messages
from django.contrib.auth import authenticate, logout
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import generate_token


# Create your views here.


def index(request: HttpRequest) -> HttpResponse:
    return render(request, "Instaurant/index.html")


def about(request: HttpRequest) -> HttpResponse:
    return HttpResponse("Hi")


def menu(request: HttpRequest) -> HttpResponse:
    return HttpResponse("menu")


def order(request: HttpRequest) -> HttpResponse:
    return HttpResponse("order")


def contact(request: HttpRequest) -> HttpResponse:
    # messages.success(request, 'Get in touch with me!!')
    if request.method == "POST":
        name: str = request.POST["name"]  # type: ignore
        email: str = request.POST["email"]  # type: ignore
        phone: str = request.POST["phone"]  # type: ignore
        content: str = request.POST["content"]  # type: ignore

        if name == "":
            messages.error(request, "You must enter your name!!")
        elif email == "":
            messages.error(request, "Please enter your email!!")
        elif phone == "":
            messages.error(request, "Please enter your phone number!!")
        elif content == "":
            messages.error(request, "Please enter your message!!")
        else:
            contact = Contact(name=name, email=email, phone=phone, content=content)
            contact.save()
            messages.success(request, "Your message has been conveyed!!")

            subject = "Contact from AM-Blogs!!"
            message = f"{contact.name} <{contact.email}> Instaurants {contact.content}"
            from_email = settings.EMAIL_HOST_USER
            to_list = ["siddhesh.agarwal@gmail.com", "727721eucs144@skcet.ac.in"]
            send_mail(subject, message, from_email, to_list, fail_silently=True)

    return render(request, "blog/contact.html")


def search(request: HttpRequest) -> HttpResponse:
    query = request.GET["query"]  # type: ignore
    if isinstance(query, str) and len(query) > 70:
        allPosts = Post.objects.none()
    else:
        allPostsTitle = Post.objects.filter(title__icontains=query)
        allPostsContent = Post.objects.filter(content__icontains=query)
        allPosts = allPostsTitle.union(allPostsContent)

    if allPosts.count() == 0:
        messages.warning(request, "No search results found. Please refine your query.")
    context = {"allPosts": allPosts, "query": query}  # type: ignore
    return render(request, "blog/search.html", context)  # type: ignore


def signup(request: HttpRequest) -> HttpResponse:
    return render(request, "signup.html")


def login(request: HttpRequest) -> HttpResponse:
    return render(request, "login.html")


def handleSignup(
    request: HttpRequest,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect | HttpResponse:
    if request.method == "POST":
        fname: str | None = request.POST.get("fname")
        lname: str | None = request.POST.get("lname")
        # address1: str | None = request.POST.get("address1")
        # address2: str | None = request.POST.get("address2")
        # city: str | None = request.POST.get("city")
        # contact: str | None = request.POST.get("contact")
        email: str | None = request.POST.get("email")
        pass1: str | None = request.POST.get("pass1")
        pass2: str | None = request.POST.get("pass2")

        # Check for erroneous inputs
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect("index")

        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect("index")

        # Check if email already exists
        myuser = User.objects.create_user(email, pass1)  # type: ignore
        myuser.first_name = str(fname)
        myuser.last_name = str(lname)
        myuser.is_active = False
        myuser.save()
        messages.success(
            request,
            "Your Account has been created succesfully!! Please check your email to confirm your email address in order to activate your account.",
        )

        # Welcome Email
        subject = "Welcome to Instaurant!!"
        message: str = f"Hello {myuser.first_name}!! \nWelcome to Instaurant!! \nThank you for visiting our website. We'll surely serve you at our best. We hope you'll love our services.\nWe have also sent you a confirmation email, please confirm your email address. \n\nThanking You"
        from_email = settings.EMAIL_HOST_USER
        to_list: list[str] = [myuser.email]

        send_mail(subject, message, from_email, to_list, fail_silently=True)

        # Email Address Confirmation Email
        current_site = get_current_site(request)
        email_subject = "Confirm your Email @Instaurant!!"
        message2 = render_to_string(
            "email_confirmation.html",
            {
                "name": myuser.first_name,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(myuser.pk)),
                "token": generate_token.make_token(myuser),
            },
        )
        send_mail(email_subject, message2, from_email, to_list, fail_silently=True)

        return redirect("index")
    return HttpResponse("404- Not Found")


def handleLogin(
    request: HttpRequest,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect | HttpResponse:
    if request.method == "POST":
        email: str | None = request.POST.get("email")
        pass1: str | None = request.POST.get("pass1")

        user = authenticate(username=email, password=pass1)

        if user is not None:
            from django.contrib.auth import login

            login(request, user)
            messages.success(request, "Logged In Successfully!!")
            return redirect("index")
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect("index")

    return HttpResponse("404")  # if request method is not 'post'


def handleLogout(
    request: HttpRequest,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect:
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect("Home")

    # return HttpResponse("Logged Out")


def postComment(
    request: HttpRequest,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect | None:
    if request.method == "POST":
        comment = request.POST.get("comment")
        user = request.user
        postSno = request.POST.get("postSno")
        post = Post.objects.get(sno=postSno)
        parentSno = request.POST.get("parentSno")

        if parentSno == "":
            comment = BlogComment(comment=comment, user=user, post=post)
            comment.save()
            messages.success(request, "Your comment has been posted!!")
        else:
            parent = BlogComment.objects.get(sno=parentSno)
            comment = BlogComment(comment=comment, user=user, post=post, parent=parent)
            comment.save()
            messages.success(request, "Your reply has been posted!!")
        return redirect(f"/{post.slug}")


def series(request: HttpRequest) -> HttpResponse:
    allseries = Series.objects.all()
    print(allseries)
    context = {"allseries": allseries}
    return render(request, "blog/series.html", context)


# series slug should be equal to series_name of the post in order to render properly


def series_list(request: HttpRequest, ser_slug) -> HttpResponse | None:  # type: ignore
    # ser_post = Series.objects.filter(ser_slug=ser_slug).values()
    ser_post_done = Post.objects.filter(series_name=ser_slug).values()

    for ser in ser_post_done:
        if ser_slug == ser["series_name"]:
            series_name = ser["series_name"]
            slug_final = ser["slug"]
            context = {
                "ser_post_done": ser_post_done,
                "slug_final": slug_final,
                "series_name": series_name,
            }
            return render(request, "blog/series_list.html", context)


def activate(
    request: HttpRequest,
    uidb64: bytes | str,
    token: str | None = None,
) -> HttpResponseRedirect | HttpResponsePermanentRedirect | HttpResponse:
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        myuser: User | None = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        myuser = None

    if myuser is not None and generate_token.check_token(myuser, token):
        from django.contrib.auth import login

        myuser.is_active = True
        myuser.save()
        login(request, myuser)
        messages.success(request, "Your Account has been activated!!")
        return redirect("Home")
    else:
        return render(request, "activation_failed.html")
