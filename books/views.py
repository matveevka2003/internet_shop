from django.contrib.auth import logout, login
from django.views.generic import ListView, DetailView
from django.shortcuts import render, redirect
from books.models import *
from django.contrib import messages
from django.db.models import Q
from users.forms import RegisterForm, LoginForm, UserChangeForm
from cart.forms import CartAddBookForm
from django.contrib.auth import get_user_model
from .forms import CommentForm
User = get_user_model()


def change_profile(request):
    """Изменение данных пользователя"""
    if request.method == 'POST':
        form = UserChangeForm(request.POST)
        if form.is_valid():
            request.user.name = form.cleaned_data['name']
            request.user.surname = form.cleaned_data['surname']
            request.user.save()
            messages.success(request, 'Данные профиля успешно изменены')
            return redirect('profile', pk=request.user.pk)
        else:
            messages.error(request, 'Ошибка изменение данных')
    else:
        form = UserChangeForm()
    return render(request, 'books/change_profile.html', {'title': 'Изменение профиля', 'form': form})


class Profile(DetailView):
    model = User
    template_name = 'books/profile.html'
    context_object_name = 'user'

    def get_context_data(self, *, object_list=None, **kwargs):
        """Добавляет в существующий контекст новые данные"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Личный кабинет'
        return context


class BookOrdering(ListView):
    model = Book
    template_name = 'books/home.html'
    context_object_name = 'books'
    paginate_by = 12

    def get_ordering(self):
        ordering = self.kwargs['order']
        return ordering

    def get_context_data(self, *, object_list=None, **kwargs):
        """Добавляет в существующий контекст новые данные"""
        context = super().get_context_data(**kwargs)
        order_by = self.kwargs['order']
        if order_by == '-rating':
            order_by = 'рейтингу (по убыванию)'
        if order_by == 'rating':
            order_by = 'рейтингу (по возрастанию)'
        if order_by == 'price':
            order_by = 'цене (по возрастанию)'
        if order_by == '-price':
            order_by = 'цене (по убыванию)'
        if order_by == 'year':
            order_by = 'году издания (по возрастанию)'
        if order_by == '-year':
            order_by = 'году издания (по убыванию)'
        context['title'] = 'Сортировка по ' + order_by
        context['cart_book_form'] = CartAddBookForm()
        return context


class SearchResultsView(ListView):
    """Возвращает queryset с результатами поиска на 'books/found_books.html'"""

    # Не работает пагинация, поэтому показываю только 12 результатов поиска

    model = Book
    context_object_name = 'books'
    template_name = 'books/found_books.html'
    search_word = ''

    def get_context_data(self, *, object_list=None, **kwargs):
        """Добавляет в существующий контекст новые данные"""
        context = super().get_context_data(**kwargs)
        context['title'] = 'Поиск ' + '"' + self.search_word + '"'
        context['search_word'] = self.search_word
        context['cart_book_form'] = CartAddBookForm()
        return context

    def get_queryset(self):
        query = self.request.GET.get('search').strip()
        if len(query) < 3:
            messages.error(self.request, 'Введено пустое поле для поиска или строка поиска содержит менее '
                                         '3 символов, в связи с чем поиск был приостановлен.')
            return Book.objects.none()
        self.search_word = query
        object_list = Book.objects.filter(
            # не понятно как, но iregex работает как мне нужно
            # разобраться, что это такое
            Q(title__iregex=query) | Q(author__iregex=query)
        )
        if len(object_list) == 0:
            messages.error(self.request,
                           'По запросу ' + '"' + self.request.GET.get('search') + '"' + ' ничего не найдено')
            return Book.objects.none()
        return object_list[:12]


def register(request):
    """Регистрация пользователя"""
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Вы успешно зарегистрировались')
            return redirect('profile', pk=request.user.pk)
        else:
            messages.error(request, 'Ошибка регистрации')
    else:
        form = RegisterForm()
    return render(request, 'books/register.html', {'title': 'Регистрация', 'form': form})


def user_login(request):
    """Вход"""
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Вы успешно вошли')
            return redirect('home')
        else:
            messages.error(request, 'Ошибка входа')
    else:
        form = LoginForm()
    return render(request, 'books/login.html', {'title': 'Вход', 'form': form})


def user_logout(request):
    """Выход"""
    logout(request)
    messages.info(request, 'Вы вышли из аккаунта')
    return redirect('login')


class HomeShop(ListView):
    """Возвращает список с книгами, который доступны для покупки"""
    model = Book
    template_name = 'books/home.html'
    context_object_name = 'books'
    paginate_by = 12

    # количество новостей на странице

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Главная'
        context['cart_book_form'] = CartAddBookForm()
        return context

    def get_queryset(self):
        return Book.objects.filter(available=True)


class BooksByCategory(ListView):
    """Возвращает список книг из выбранной категории"""
    model = Book
    template_name = 'books/home.html'
    context_object_name = 'books'
    # изменяет дефолтное название объекта
    allow_empty = False
    # запрещает показывать пустые списки (выводит ошибку 404, если нет книг в заданной категории)
    paginate_by = 12

    # количество новостей на странице

    def get_context_data(self, *, object_list=None, **kwargs):
        """Добавляет в существующий контекст новые данные"""
        context = super().get_context_data(**kwargs)
        context['title'] = Category.objects.get(pk=self.kwargs['category_id'])
        context['cart_book_form'] = CartAddBookForm()
        return context

    def get_queryset(self):
        return Book.objects.filter(category_id=self.kwargs['category_id'], available=True)


class BooksByAuthor(ListView):
    """Возвращает список книг выбранного автора"""
    model = Book
    template_name = 'books/home.html'
    context_object_name = 'books'
    # изменяет дефолтное название объекта
    allow_empty = False
    paginate_by = 12

    # количество новостей на странице

    def get_context_data(self, *, object_list=None, **kwargs):
        """Добавляет в существующий контекст новые данные"""
        context = super().get_context_data(**kwargs)
        for item in Book.objects.filter(author=self.kwargs['author']):
            context['title'] = item.author
            break
        context['cart_book_form'] = CartAddBookForm()
        return context

    def get_queryset(self):
        return Book.objects.filter(author=self.kwargs['author'], available=True)


def view_book(request, pk):
    """Возвращает единственную выбранную книгу и добавляет форму для комментариев"""
    book = Book.objects.get(pk=pk)
    if request.method == 'POST':
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            new_comment.book = book
            new_comment.user = request.user
            new_comment.save()
            messages.success(request, 'Ваш отзыв был добавлен')
            return redirect('view_book', pk)
        else:
            messages.error(request, 'Ошибка добавления отзыва')
    else:
        comment_form = CommentForm()
    return render(request, 'books/view_book.html', {
        'item': book,
        'title': book,
        'cart_book_form': CartAddBookForm(),
        'comments': book.comments.filter(active=True),
        'comment_form': comment_form,
    })
