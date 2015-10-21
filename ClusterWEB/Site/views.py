#!/usr/bin/python
# -*- coding: utf-8 -*-
import codecs
from abc import ABCMeta
from overloading import overloaded
from math import *
from collections import Counter
from scipy import *
from nltk.stem.snowball import EnglishStemmer, RussianStemmer
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.core.urlresolvers import reverse
from django import forms
from grab import Grab
from django.utils.http import urlquote_plus
from Site import models


class SearchForm(forms.Form):
    search_request = forms.CharField(widget=forms.TextInput(attrs={'size': 140, 'lang': 50, 'width': 40,
                                                                   'placeholder': "Поиск..."}))


def main_page(request):
    form = SearchForm(request.GET, auto_id=False, initial={'search_request': 'Введите поисковый запрос'})
    # Выполнение поиска
    if form.is_valid():
        query = form.cleaned_data['search_request']
        return HttpResponseRedirect('/search/results/request=' + urlquote_plus(query) + '&group=1/')

    return render(request, "Site/Main_Page.html", {'form': form})


def main_page_runserver(request):
    return HttpResponseRedirect('/search/')


def search_page_redirect(request, query):
    return HttpResponseRedirect('/search/results/request=' + str(query) + '&group=1/')


def search_page(request, query, group):
    form = SearchForm(request.GET, auto_id=False, initial={'search_request': 'Введите поисковый запрос'})
    form.search_request = query
    result_list = yandex_search(query, group)
    clusters = clustering_search_results(result_list)
    if form.is_valid():
        query = form.cleaned_data['search_request']
        return HttpResponseRedirect('/search/results/request=' + str(urlquote_plus(query)) + '&group='+str(group)+'/')
    return render(request, "Site/Result_Page.html", {'form': form, 'clusters': clusters}, )


def yandex_search(query, group):
    g = Grab()
    g.setup(connect_timeout=20, timeout=20)
    titles = []
    urls = []
    snippets = []
    result_list = []

    def replacement(string):
        return string.replace('\u2014', '-').replace('\u0301', '').replace('\u2013', '-')

    page = 2*int(group)-2
    while page < 2:

        yandex_url = 'http://yandex.ru/yandsearch?text=%s&numdoc=50' % urlquote_plus(query)
        if page:
            yandex_url += '&p=%d' % page
        try:
            g.go(yandex_url)
        except:
            g.change_proxy()
        # Получение информации (Заголовков, адресов ссылок и сниппетов) со страницы Яндекса с помощью XPath выражения
        sel_urls = g.doc.select('//div[@class="serp-list" and @role="main"]/' +
                                'div[contains(@class,"serp-block serp-block")' +
                     ' and not(contains(@class,"images")) and not(contains(@class,"video"))]//' +
                     'h2[@class="serp-item__title"]/a/@href')
        sel_titles = g.doc.select('//div[@class="serp-list" and @role="main"]/div[contains(@class,' +
                                  '"serp-block serp-block")' +
                      ' and not(contains(@class,"images")) and not(contains(@class,"video"))]' +
                      '//h2[@class="serp-item__title"]')
        sel_snippets = g.doc.select('//div[@class="serp-list" and @role="main"]/' +
                                    'div[contains(@class,"serp-block serp-block")' +
                          ' and not(contains(@class,"images")) and not(contains(@class,"video"))]' +
                          '//div[contains(@class,"__text") or contains(@class,"__descr")]')

        for elem in sel_urls.selector_list:
            urls.append(elem._node)
        for elem in sel_titles.selector_list:
            titles.append(replacement(elem.text()))
        for elem in sel_snippets.selector_list:
            snippets.append(replacement(elem.text()))
        page += 1
    for i in range(len(titles)):
        result_list.append(Search_Result(titles[i], urls[i], snippets[i], i))
    return result_list

def clustering_search_results(results):
    if len(results):
        tool_text = TextOperations()
        for i in range(len(results)):
            tool_text.Tag.append(tool_text.frequency(tool_text.vClusterize(results[i].text)))
        tool_text.form_matrix()
        tool_cluster = Clusters(tool_text.Matrix, tool_text.TextTitles, tool_text.Words)
        tool_cluster.ClusterSelection(0, 10)
        tag_list = tool_cluster.GetWdsFromClst()
        text_list = tool_cluster.GetTxtsFromClst()
        webclusters = []
        for i in range(len(tag_list)):
            tag_temp_list = []
            result_temp_list = []
            for tag in tag_list:
                tag_temp_list.append(tag)
            for item in text_list:
                temp_index = int(item) - 1
                result_temp_list.append(results[temp_index])
            webclusters.append(webCluster(i, tag_temp_list, result_temp_list))
        return webclusters
    else:
        return []



class Search_Result:
    def __init__(self, title, url, snippet, num):
        self.id = num
        self.title = title
        self.url = url
        self.snippet = snippet
        self.text = self.title + ' ' + self.snippet

stop_words_eng = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0",
                  "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t",
                  "u", "v", "w", "x", "y", "z",
                  "about", "above", "according", "across", "actually", "ad", "adj", "ae", "af", "after", "afterwards",
                  "ag", "again", "against", "ai", "al", "all", "almost", "alone", "along", "already", "also",
                  "although", "always", "am", "among", "amongst", "an", "and", "another", "any", "anyhow", "anyone",
                  "anything", "anywhere", "ao", "aq",
                  "ba", "bb", "bd", "be", "became", "because", "become", "becomes", "becoming", "been", "before",
                  "beforehand", "begin", "beginning", "behind", "being", "below", "beside", "besides", "between",
                  "beyond", "bf", "bg", "bh", "bi", "billion", "bj", "bm", "bn", "bo", "both",
                  "br", "bs", "bt", "but", "buy", "bv", "bw", "by", "bz", "ca", "can", "can't", "cannot", "caption",
                  "cc", "cd", "cf", "cg", "ch", "ci", "ck", "cl", "click", "cm", "cn", "co", "co.", "com", "copy",
                  "could", "couldn", "couldn't", "cr", "cs", "cu", "cv", "cx", "cy", "cz",
                  "de", "did", "didn", "didn't", "dj", "dk", "dm", "do", "does", "doesn", "doesn't",
                  "don", "don't", "down", "during", "dz",
                  "each", "ec", "edu", "ee", "eg", "eh", "eight", "eighty", "either", "else", "elsewhere", "end",
                  "ending", "enough", "er", "es", "et", "etc", "even", "ever", "every", "everyone", "everything",
                  "everywhere", "except",
                  "few", "fi", "fifty", "find", "first", "five", "fj", "fk", "fm", "fo", "for", "former", "formerly",
                  "forty", "found", "four", "fr", "free", "from", "further", "fx",
                  "ga", "gb", "gd", "ge", "get", "gf", "gg", "gh", "gi", "gl", "gm", "gmt", "gn", "go", "gov", "gp",
                  "gq", "gr", "gs", "gt", "gu", "gw", "gy",
                  "had", "has", "hasn", "hasn't", "have", "haven", "haven't", "he", "he'd", "he'll", "he's",
                  "help", "hence", "her", "here", "here's", "hereafter", "hereby", "herein", "hereupon", "hers",
                  "herself", "him", "himself", "his", "hk", "hm", "hn", "home", "homepage", "how", "however",
                  "hr", "ht", "htm", "html", "http", "hu", "hundred",
                  "i'd", "i'll", "i'm", "i've", "i.e.", "id", "ie", "if", "ii", "il", "im", "in", "inc", "inc.",
                  "indeed", "information", "instead", "int", "into", "io", "iq", "ir", "is", "isn", "isn't",
                  "it", "it's", "its", "itself",
                  "je", "jm", "jo", "join", "jp",
                  "ke", "kg", "kh", "ki", "km", "kn", "koo", "kp", "kr", "kw", "ky", "kz",
                  "la", "last", "later", "latter", "lb", "lc", "least", "less", "let", "let's", "li", "like",
                  "likely", "lk", "ll", "lr", "ls", "lt", "ltd", "lu", "lv", "ly",
                  "ma", "made", "make", "makes", "many", "maybe", "mc", "md", "me", "meantime", "meanwhile", "mg", "mh",
                  "might", "mil", "million", "miss", "mk", "ml", "mm", "mn", "mo",
                  "more", "moreover", "most", "mostly", "mp", "mq", "mr", "mrs", "ms", "msie", "mt", "mu", "much",
                  "must", "mv", "mw", "mx", "my", "myself", "mz",
                  "na", "namely", "nc", "ne", "neither", "net", "netscape", "never", "nevertheless", "new",
                  "next", "nf", "ng", "ni", "nine", "ninety", "nl", "no", "nobody", "none", "nonetheless", "noone",
                  "nor", "not", "nothing", "now", "nowhere", "np", "nr", "nu", "null", "nz",
                  "of", "off", "often", "om", "on", "once", "one", "one's", "only", "onto", "or", "org", "other",
                  "others", "otherwise", "our", "ours", "ourselves", "out", "over", "overall", "own",
                  "pa", "page", "pe", "per", "perhaps", "pf", "pg", "ph", "pk", "pl", "pm", "pn", "pr", "pt", "pw",
                  "py",
                  "qa",
                  "rather", "re", "recent", "recently", "reserved", "ring", "ro", "ru", "rw",
                  "sa", "same", "sb", "sc", "sd", "se", "seem", "seemed", "seeming", "seems",
                  "seven", "seventy", "several", "sg", "sh", "she", "she'd",
                  "she'll", "she's", "should",
                  "shouldn", "shouldn't", "si", "since", "site", "six", "sixty", "sj", "sk", "sl", "sm", "sn", "so",
                  "some", "somehow", "someone", "something", "sometime", "sometimes",
                  "taking", "tc", "td", "ten", "text", "tf", "tg", "test", "th", "than", "that", "that'll", "that's",
                  "the", "their", "them", "themselves", "then", "thence", "there", "there'll", "there's",
                  "thereafter", "thereby", "therefore", "therein", "thereupon", "these", "they", "they'd",
                  "they'll", "they're", "they've", "thirty", "t",
                  "ua", "ug", "uk", "um", "under", "unless", "unlike", "unlikely", "until", "up", "upon", "us", "use",
                  "used", "using", "uy", "uz",
                  "va", "vc", "ve", "very", "vg", "vi", "via", "vn", "vu",
                  "was", "wasn", "wasn't", "we", "we'd", "we'll", "we're", "we've", "web", "webpage", "website",
                  "welcome", "well", "were", "weren", "weren't", "wf", "what", "what'll", "what's", "whatever",
                  "when", "whence", "whenever", "where", "whereafter", "whereas", "whereby", "wherein", "whereupon",
                  "wherever", "whether", "which",
                  "ye", "yes", "yet", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
                  "yourself", "yourselves", "yt", "yu",
                  "za", "zm", "zr"]

stop_words_rus_full = ["a",
                       "б", "бы", "будто",
                       "в", "вам", "вас", "во", "всех", "всегда", "ведь", "вот", "впрочем", "вдруг",
                       "где",
                       "даже", "до", "для", "да",
                       "ее", "есть", "ему", "его", "ее", "ей", "если", "еще",
                       "ж", "же",
                       "за",
                       "из", "и", "из-за", "или", "иногда", "иль",
                       "к", "ко", "кто", "как", "кому", "кого", "кем", "когда", "куда"
                                                                                "либо", "ли",
                       "может", "между", "меня", "мне", "мы", "мной",
                       "но", "него", "нет", "них", "ну", "надо", "наконец", "нас", "на", "нибудь", "ним", "ни", "не",
                       "например",
                       "о", "об", "однако",
                       "по", "при", "перед", "пред", "под", "про",
                       "со", "с",
                       "ты", "там", "тот", "тех", "тут", "то", "та", "том", "той", "тому", "того", "тобой", "тебя",
                       "теперь",
                       "у",
                       "что", "чем", "чему", "чего"
                                             "этот",
                       "я"]

stop_words_rus_stem = ["б", "без", "буд", "больш", "был",
                       "в", "вам", "вас", "во", "вс", "всех", "всегда", "ведь", "вот", "впрочем", "вдруг", "вмест",
                       "говор",
                       "дел",
                       "здес", "зач", "з", "занима",
                       "им", "иногд", "ил",
                       "к", "ко", "кто", "как", "котор",
                       "мен", "мног", "мож", "мог", "можн", "м", "мы",
                       "наш", "н", "нибуд", "ним", "называ", "назван", "назва", "нам",
                       "от", "он", "обычн", "основа",
                       "побыва", "п",
                       "р",
                       "сам", "св", "сво", "себ", "сказа", "скаж", "стат", "стал", "станов",
                       "тем", "так", "теб",
                       "уж",
                       "чтоб", "част",
                       "эт",
                       "явля"]


class Cluster:
    Data = []

    def GetWds(self):
        result = []
        cst = Word(" ")
        for i in range(len(self.Data)):
            if type(self.Data[i].Data) == type(cst):
                result.append(self, self.Data[i].Data)
        return result

    def GetTxts(self):
        result = []
        cst = TextTitle("1")
        for i in range(len(self.Data)):
            if type(self.Data[i].Data) == type(cst):
                result.append(self, self.Data[i].Data)
        for i in range(len(result - 1)):
            for j in range(len(result) - i - 1):
                if int(result[j].Data.GetTag()) > int(result[j+1].Data.GetTag()):
                    a = result[j+1]
                    result[j+1] = result[j]
                    result[j] = a
        return result

class webCluster:
    def __init__(self, id, tags, results):
        self.id = str(id + 1)
        self.tags = tags
        self.results = results

class Clusters:
    G = None
    longestEdgeindex = int()
    slongestEdgeindex = int()
    lEdgeWeight = float()
    slEdgeWeight = float()
    C = []
    Texts = Cluster()
    textTitles = []

    def __init__(self, A, texts, words):
        self.textTitles = texts
        self.C = []
        self.G = Graph()
        self.Texts = Cluster()
        # Сингулярного разложение частотной матрицы A:
        W, U, VT = linalg.svd(A)
        # добавление вершин графа:
        for i in range(len(U)):
            self.G.V.append(Vertex(words[i], U[i, 0], U[i, 1], U[i, 2]))
        for i in range(len(VT[0])):
            self.G.V.append(Vertex(texts[i], VT[0, i], VT[1, i], VT[2, i]))
        # Добавление ребер графа:
        for i in range(len(self.G.V)):
            for j in range(i + 1, len(self.G.V)):
                self.G.E.append(Edge(self.G.V[i], self.G.V[j]))
        for i in range(len(texts)):
            for j in range(len(self.G.V)):
                if texts[i].GetTag == self.G.V[j].Data.GetTag:
                    self.Texts.Data.append(self.G.V[j])

    def ClusterSelection(self, k, n):
        self.G.find_min_span_tree(self.G.V[0])
        for i in range(len(self.G.E)):
            if not self.G.optimal:
                self.G.E.remove(self.G.E[i])
                i -= 1
        self.LongestEdge()
        if n == 1:
            while self.lEdgeWeight > k * self.slEdgeWeight and len(self.G.E) != 1:
                self.G.E.remove(self.G.E[self.longestEdgeindex])
                self.LongestEdge()
        elif n == 2:
            while self.lEdgeWeight > k * self.AverageEdgeWeight(self.G.E) and len(self.G.E) != 1:
                self.G.E.remove(self.G.E[self.longestEdgeindex])
                self.LongestEdge()
        else:
            temp = self.FindMode(self.G.E)
            while self.lEdgeWeight > k * temp and len(self.G.E) != 1:
                self.G.E.remove(self.G.E[self.longestEdgeindex])
                self.LongestEdge()
        self.Clusterize()
        for i in range(len(self.C)):
            if len(self.C[i].Data) < 1:
                self.C.remove(self.C[i])
                i -= 1
        for i in range(len(self.C)):
            if self.ConsistsOfTexts(self.C[i]):
                self.AddToClosestCluster(self.C[i])
                i -= 1
        for i in range(len(self.C)):
            if self.ConsistsOfWords(self.C[i]):
                self.AddToClosestCluster(self.C[i])
                i -= 1

    def LongestEdge(self):
        if len(self.G.E) > 1:
            self.longestEdgeindex = 0
            self.lEdgeWeight = self.G.E[0].Weight
            for i in range(len(self.G.E)):
                if self.G.E[i].Weight > self.lEdgeWeight:
                    self.slEdgeWeight = self.lEdgeWeight
                    self.slongestEdgeindex = self.longestEdgeindex
                    self.lEdgeWeight = self.G.E[i].Weight
                    self.longestEdgeindex = i
            for i in range(len(self.G.E)):
                if i != self.longestEdgeindex:
                    if self.G.E[i].Weight > self.slEdgeWeight & self.G.E[i].Weight != self.lEdgeWeight:
                        self.slEdgeWeight = self.G.E[i].Weight
                        self.slongestEdgeindex = i

    def AverageEdgeWeight(self, a):
        sum = float(0)
        for i in range(len(a)):
            sum += a[i].Weight
        return sum / len(a)

    def Clusterize(self):
        self.C = []
        for i in range(len(self.G.V)):
            exists = False
            for j in range(len(self.C)):
                tobreak = False
                for k in range(len(self.C[j].Data)):
                    if self.G.V[i] == self.C[j].Data[k]:
                        exists = True
                        tobreak = True
                        break
                if tobreak:
                    break
                if not exists:
                    self.C.append(Cluster())

    def ClusterizeStep(self, cl, v, firststep):
        if firststep:
            for i in range(len(self.G.E)):
                if self.G.E[i].V1 == v:
                    self.ClusterizeStep(cl, self.G.E[i].V2, 0)
                elif self.G.E[i].V2 == v:
                    self.ClusterizeStep(cl, self.G.E[i].V1, 0)
        else:
            exists = False
            for k in range(len(cl.Data)):
                if v == cl.Data[k]:
                    exists = True
                    break
            if exists == 0:
                cl.Data.append(v)
                for i in range(len(self.G.E)):
                    if self.G.E[i].V1 == v:
                        self.ClusterizeStep(cl, self.G.E[i].V2, 0)
                    elif self.G.E[i].V2 == v:
                        self.ClusterizeStep(cl, self.G.E[i].V1, 0)

    @overloaded
    def AddToClosestCluster(self, v):
        temp = Graph(self.G.V)
        for i in range(len(temp.V)):
            for j in range(i + 1, len(temp.V)):
                temp.E.append(Edge(temp.V[i], temp.V[j]))
        neighbour = self.G.V[0]
        shortestedgeweight = 340282300000000000000000000000000000000
        for i in range(len(temp.E)):
            if temp.E[i].V1 == v:
                if temp.E[i].Weight < shortestedgeweight:
                    shortestedgeweight = temp.E[i].Weight
                    neighbour = temp.E[i].V2
            elif temp.E[i].V2 == v:
                if temp.E[i].Weight < shortestedgeweight:
                    shortestedgeweight = temp.E[i].Weight
                    neighbour = temp.E[i].V1
        for i in range(len(self.C)):
            for j in range(len(self.C[i].Data)):
                if self.C[i].Data[j] == neighbour:
                    self.C[i].append(v)

    @overloaded
    def AddToClosestCluster(self, cl):
        temp = Graph(self.G.V)
        for i in range(len(temp.V)):
            for j in range(i + 1, len(temp.V)):
                temp.E.append(Edge(temp.V[i], temp.V[j]))
        neighbour = self.G.V[0]
        shortestedgeweight = 340282300000000000000000000000000000000
        for j in range(len(cl.Data)):
            for i in range(len(temp.E)):
                if temp.E[i].V1 == cl.Data[j]:
                    if temp.E[i].Weight < shortestedgeweight:
                        access = True
                        for q in range(len(cl.Data)):
                            if temp.E[i].V2 == cl.Data[q] and q != j:
                                access = False
                        if access:
                            shortestedgeweight = temp.E[i].Weight
                            neighbour = temp.E[i].V2
                elif temp.E[i].V2 == cl.Data[j]:
                    if temp.E[i].Weight < shortestedgeweight:
                        access = True
                        for q in range(len(cl.Data)):
                            if temp.E[i].V1 == cl.Data[q] and q != j:
                                access = False
                        if access:
                            shortestedgeweight = temp.E[i].Weight
                            neighbour = temp.E[i].V1
        for i in range(len(self.C)):
            tobreak = False
            for j in range(len(self.C[i].Data)):
                if self.C[i].Data[j] == neighbour:
                    for q in range(len(cl.Data)):
                        self.C[i].Data.append(cl.Data[q])
                    self.C.remove(cl)
                    tobreak = True
                    break
            if tobreak:
                break

    def ConsistsOfTexts(self, cl):
        allexist = True
        for i in range(len(cl.Data)):
            oneoftexts = False
            for j in range(len(self.Texts.Data)):
                if cl.Data[i].Data.Tag == self.Texts.Data[j].Data.Tag:
                    oneoftexts = True
            if not oneoftexts:
                allexist = False
                break
        return allexist

    def ConsistsOfWords(self, cl):
        ofwds = True
        oneoftexts = 0
        for i in range(len(cl.Data)):
            for j in range(len(self.Texts.Data)):
                if cl.Data[i].Data.GetTag == self.Texts.Data[j].Data.GetTag:
                    oneoftexts += 1
        if oneoftexts > 1 and len(cl.Data) > oneoftexts + 2:
            ofwds = False
        return ofwds

    def FindMode(self, sourse):
        v = 5
        le = -1
        se = 340282300000000000000000000000000000000
        for i in range(len(sourse)):
            if sourse[i].Weight < se:
                se = sourse[i].Weight
            if sourse[i].Weight > le:
                le = sourse[i].Weight
        gaps = []
        for i in range(v):
            gaps.append([])
        av = float((le - se) / v)
        for i in range(1, v):
            for j in range(len(sourse)):
                if sourse[j].Weight > (i * av + se) and sourse[j].Weight <= ((i +1) * av + se):
                    gaps[i].append(sourse[j])
        gindex = 0
        a = len(gaps[gindex])
        for i in range(len(gaps)):
            if len(gaps[i]) > a:
                gindex = i
                a = len(gaps[i])
        return self.AverageEdgeWeight(gaps[gindex])

    def GetWdsFromClst(self):
        result = []
        for i in range(len(self.C)):
            result.append(self.C[i].GetWds())
        return result

    def GetTxtsFromClst(self):
        result = []
        for i in range(len(self.C)):
            result.append(self.C[i].GetTxts())
        return result


class Edge:
    optimal = False

    def __init__(self, V1, V2):
        self.V1 = V1
        self.V2 = V2
        self.Weight = sqrt((V1.x-V2.x)**2+(V1.y-V2.y)**2+(V1.z-V2.z)**2)


class Graph:
    max = 340282300000000000000000000000000000000
    # float.maxvalue=340282300000000000000000000000000000000

    @overloaded
    def init(self, l):
        self.V = l
        self.E = []

    @overloaded
    def __init__(self):
        self.V = []
        self.E = []

    def find_min_span_tree(self, first):
        first.t = 0
        temp = first
        Q = []
        while self.max_marker_exists():
            temp = self.min_temporary_marker()
            temp.p = temp.t
            neighbours = []
            self.finding_neighbours(neighbours, temp)
            self.change_temporary_marker(neighbours, temp)
            Q.append(temp)
            for i in range(1, len(Q)):
                e = self.find_edge(Q[i], Q[i].prev)
                e.optimal = True

    def max_marker_exists(self):
        for i in range(0, len(self.V)):
            if self.V[i].p == self.max:
                return True
        return False

    def min_temporary_marker(self):
        temp = None
        for i in range(0, len(self.V)):
            if not self.V[i].wasMin:
                temp = self.V[i]
                break
        for i in range(0, len(self.V)):
            temp = self.V[i] if self.V[i].t <= temp.t and self.V[i].p == self.max else None

        temp.wasMin = True
        return temp

    def finding_neighbours(self, l, temp):
        for j in range(0, len(self.E)):
            if self.E[j].V1 == temp and self.E[j].V2.p == self.max:
                l.append(self.E[j].V2)
            elif self.E[j].V2 == temp and self.E[j].V1.p == self.max:
                l.append(self.E[j].V1)

    def change_temporary_marker(self, l, temp):
        w = 0
        for i in range(len(l)):
            w = float(self.find_edge(l[i], temp).Weight)
            if l[i].t > w:
                l[i].t = float(w)
                l[i].prev = temp

    def find_edge(self, v1, v2):
        temp = None
        for j in range(len(self.E)):
            if self.E[j].V1 == v1 and self.E[j].V2 == v2 or self.E[j].V2 == v1 and self.E[j].V1 == v2:
                temp = self.E[j]
        return temp


class Tags(metaclass=ABCMeta):
    def GetTag(self):
        pass


class TextOperations:
    stemmer_eng = EnglishStemmer()
    stemmer_rus = RussianStemmer()
    TextTitles = []
    Words = []
    Tag = []
    AllWords = []

    def vClusterize(self, txt):

        # Дробление текста на слова и удаление знаков препнания
        def divid(txt):

            def char_sensible(char):
                c = ord(char)
                return 1040 <= c <= 1071 or 65 <= c <= 90 or 1072 <= c <= 1103 or 97 <= c <= 122 or 48 <= c <= 57

            def word_sensible(word):
                for i in range(len(word)):
                    if char_sensible(word[i]):
                        return True
                return False

            def punctuation_delete(word):
                while not char_sensible(word[0]):
                    word = word[1:]
                while not char_sensible(word[-1]):
                    word = word[:-1]
                return word

            txt.lower()
            txt.replace('ё', 'е')
            text = txt.split()
            for i in range(0, len(text)):
                if word_sensible(text[i]):
                    text[i] = punctuation_delete(text[i])
                else:
                    text.remove(text[i])
                    i -= 1
            return text

        # Проверка слова на язык (русский или английский (алфавит - кириллица или латиница?))
        def language_check(word):
            rez = "invalid"
            for k in range(len(word)):
                if 1072 <= ord(word[k]) <= 1103:
                    if rez == "cyrillic" or rez == "invalid":
                        rez = "cyrillic"
                    elif rez == "latin":
                        rez = "invalid"
                        break
                elif 97 <= ord(word[k]) <= 122:
                    if rez == "latin" or rez == "invalid":
                        rez = "latin"
                    elif rez == "cyrillic":
                        rez = "invalid"
                        break
            return rez

        text = divid(txt)
        for i in range(0, len(text)):
            language = language_check(text[i])
            if language == "cyrillic":
                if stop_words_rus_full.__contains__(text[i]):
                    text.remove(text[i])
                else:
                    item = self.stemmer_rus.stem(text[i])
                    if stop_words_rus_stem.__contains__(text[i]):
                        text.remove(text[i])
                        i -= 1
            elif language == "latin":
                if stop_words_eng.__contains__(text[i]):
                    text.remove(text[i])
                    i -= 1
                else:
                    text[i] = self.stemmer_eng.stem(text[i])
        return text

    # Формирование списка уникальных основ в тексте с указанием их частот
    @staticmethod
    def frequency(text):
        freq_list = []
        for word in text:
            existance = False
            for elem in freq_list:
                if word == elem.word:
                    elem.count += 1
                    existance = True
            if not existance:
                freq_list.append(Word(word))
        return freq_list

    def form_matrix(self):

        def llw_change():

            # Формирование списка уникальных основ слов, которые повторяются в РАЗНЫХ текстах
            def all_words():

                def check_list_item(List, Elem):
                    for i in range(0, len(List)):
                        if List[i].word == Elem:
                            List[i].IsSingle = False
                            return True
                    return False

                ss = []
                temp = []
                for i in range(0, len(self.Tag)):
                    for j in range(len(0, self.Tag[i])):
                        if not check_list_item(temp, self.Tag[i][j].word):
                            temp.append(Word(self.Tag[i][j].word))
                for elem in temp:
                    if not elem.IsSingle:
                        ss.append(elem.word)
                return ss

            self.AllWords = all_words()
            temp = []
            for i in range(0, len(self.Tag)):
                temp.append([])
                for j in range(0, len(self.AllWords)):
                    word_exists = False
                    for k in range(len(self.Tag[i])):
                        if self.AllWords[j] == self.Tag[i][k].word:
                            word_exists = True
                            temp[i].append(Word(self.Tag[i][k].word, self.Tag[i][k].count))
                            break
                    if not word_exists:
                        temp[i].append(Word(self.AllWords[j], 0))
            self.Tag = temp

        llw_change()
        self.Matrix = zeros([len(self.Tag[0]), len(self.Tag)])
        for i in range(0, len(self.Tag[0])):
            for j in range(0, len(self.Tag)):
                self.Matrix[i, j] = self.Tag[j][i].count
                self.TextTitles = TextTitle(str(j + 1))
                self.Words[i] = self.Tag[j][i]


class TextTitle(Tags):
    def __init__(self, Title):
        self.Title = Title

    def GetTag(self):
        return self.Title


class Vertex:
    # Временный и постоянный приоритетные коеффициенты
    t = p = 340282300000000000000000000000000000000
    Data = Tags()
    isin = wasMin = False
    cocheck = 0

    def __init__(self, Data, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.Data = Data


class Word(Tags):
    count = 1
    IsSingle = True

    @overloaded
    def __init__(self, word):
        self.word = word

    @overloaded
    def __init__(self, word, c):
        self.word = word
        self.count = c

    @overloaded
    def __init__(self, word, c, IsSingle):
        self.word = word
        self.IsSingle = IsSingle
        self.count = c

    def GetTag(self):
        return self.word
