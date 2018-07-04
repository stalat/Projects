# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from django.http import HttpResponse
from models import Board

def home_001(request):
    boards = Board.objects.all()
    boards_name = list()

    for board in boards:
        boards_name.append(board.name)

    response_html = "<br>".join(boards_name)

    return HttpResponse(response_html)

def home(request):
    boards = Board.objects.all()
    return render(request, "home_001.html", {"boards": boards})

def board_topics(request, pk):
    board = Board.objects.get(pk=pk)
    return render(request, 'topics.html', {'board': board})
    # return HttpResponse("This is a test template")
