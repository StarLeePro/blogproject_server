from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from tools.logging_dec import logging_check, get_user_by_request
from tools.cache_dec import cache_set
import json
from .models import Topic
from user.models import UserProfile
from django.core.cache import cache
from message.models import Message

# 异常码 10300-10399

# Create your views here.

class TopicViews(View):

    def clear_topics_caches(self, request):
        path = request.path_info
        cache_p = ['topics_cache_self_', 'topics_cache_']
        cache_h = ['', '?category=tec', '?category=no-tec']
        all_key = []
        for key_p in cache_p:
            for key_h in cache_h:
                all_key.append(key_p + path + key_h)
        print('clear caches is %s'%all_key)
        cache.delete_many(all_key)


    def make_topics_res(self, author, author_topics):
        # 通过传入的参数查询到全部内容返回，结构是json
        res = {'code': 200, 'data':{}}
        topics_res = []
        for topic in author_topics:
            d = {}
            d['id'] = topic.id
            d['title'] = topic.title
            d['category'] = topic.category
            d['created_time'] = topic.created_time.strftime("%Y-%m-%d-%H-%M-%S")
            d['introduce'] = topic.introduce
            d['author'] = author.nickname
            topics_res.append(d)

        res['data']['topics'] = topics_res
        res['data']['nickname'] = author.nickname
        return res

    def make_topic_res(self, author, author_topic, is_self):
        '''

        :param author:
        :param author_topic:
        :param is_self:
        :return: 博客详情信息 res字典
        '''
        if is_self:
            # 博主访问自己
            next_topic = Topic.objects.filter(id__gt=author_topic.id, author=author).first()  # .first()可以拿到大于当前id的第一个
            last_topic = Topic.objects.filter(id__lt=author_topic.id, author=author).last()
        else:
            next_topic = Topic.objects.filter(id__gt=author_topic.id, author=author, limit='public').first()  # .first()可以拿到大于当前id的第一个
            last_topic = Topic.objects.filter(id__lt=author_topic.id, author=author, limit='public').last()
        next_id = next_topic.id if next_topic else None
        next_title = next_topic.title if next_topic else ''
        last_id = last_topic.id if last_topic else None
        last_title = last_topic.title if last_topic else ''
        # 关联留言和回复
        all_messages = Message.objects.filter(topic=author_topic).order_by('-created_time')
        msg_list = []  # 留言
        rep_dic = {}  # 回复
        m_count = 0
        for msg in all_messages:
            if msg.parent_message:
                # 回复
                rep_dic.setdefault(msg.parent_message, [])
                rep_dic[msg.parent_message].append({'msg_id':msg.id, 'publisher':msg.publisher.nickname, 'publisher_avatar':str(msg.publisher.avatar),
                                                    'content':msg.content, 'created_time':msg.created_time.strftime('%Y-%m-%d %H:%M:%S')})
            else:
                # 留言
                m_count += 1
                msg_list.append({'id': msg.id, 'content': msg.content, 'publisher':msg.publisher.nickname, 'publisher_avatar': str(msg.publisher.avatar),
                                 'created_time':msg.created_time.strftime('%Y-%m-%d %H:%M:%S'), 'reply':[]})
        for m in msg_list:
            if m['id'] in rep_dic:
                m['reply'] = rep_dic[m['id']]


        # 组织json
        res = {'code': 200, 'data':{}}
        res['data']['nickname'] = author.nickname
        res['data']['title'] = author_topic.title
        res['data']['category'] = author_topic.category
        res['data']['created_time'] = author_topic.created_time.strftime('%Y-%m-%d %H:%M:%S')
        res['data']['content'] = author_topic.content
        res['data']['introduce'] = author_topic.introduce
        res['data']['author'] = author.nickname
        res['data']['last_id'] = last_id
        res['data']['last_title'] = last_title
        res['data']['next_id'] = next_id
        res['data']['next_title'] = next_title
        res['data']['messages'] = msg_list
        res['data']['messages_count'] = m_count
        return res

    @method_decorator(logging_check)
    def post(self, request, author_id):

        author = request.myuser
        # 取出前端数据
        json_str = request.body
        json_obj = json.loads(json_str)
        title = json_obj["title"]
        content = json_obj["content"]
        content_text = json_obj["content_text"]
        introduce = content_text[:30]
        limit = json_obj['limit']
        category = json_obj['category']
        if limit not in ['public', 'private']:
            result = {'code':10300, 'error':'the limit error~'}
            return JsonResponse(result)
        if category not in ['tec', 'no-tec']:
            result = {'code': 10301, 'error': 'the category error~'}
            return JsonResponse(result)

        # 创建topic数据
        Topic.objects.create(title=title, content=content,
                             introduce=introduce, limit=limit, category=category, author=author)
        # 删除缓存
        self.clear_topics_caches(request)

        return JsonResponse({'code':200})

    @method_decorator(cache_set(300))
    def get(self, request, author_id):
        print('---view in---')
        # /v1/topics/lixing
        # 访问者 visitor
        # 当前被访问博客的博主 author
        try:
            author = UserProfile.objects.get(username=author_id)
        except Exception as e:
            result = {'code': 10301, 'error': 'the author is not existed'}
            return JsonResponse(result)

        # 如果有token，则登录了，没token，是游客
        visitor = get_user_by_request(request)
        visitor_username = None
        if visitor:
            visitor_username = visitor.username

        t_id = request.GET.get('t_id')
        if t_id:
            # /v1/topics/lixing?t_id=1
            # 获取指定文章数据
            t_id = int(t_id)
            is_self = False
            if visitor_username == author_id:
                is_self = True
                try:
                    author_topic = Topic.objects.get(id=t_id, author_id=author_id)
                except Exception as e:
                    result = {'code': 10302, 'error': 'No topic'}
                    return JsonResponse(result)
            else:
                try:
                    author_topic = Topic.objects.get(id=t_id, author_id=author_id, limit='public')
                except Exception as e:
                    result = {'code': 10303, 'error': 'No topic'}
                    return JsonResponse(result)
            res = self.make_topic_res(author, author_topic, is_self)
            return JsonResponse(res)

        else:
            # 获取列表页数据
            # /v1/topics/lixing
            # /v1/topics/lixing?category=[tec|no-tec]
            category = request.GET.get('category')
            if category in ['tec', 'no-tec']:
                if visitor_username == author_id:
                    # 博主访问自己的博客
                    author_topics = Topic.objects.filter(author_id=author_id, category=category)
                else:
                    author_topics = Topic.objects.filter(author_id=author_id, limit='public', category=category)
            else:
                if visitor_username == author_id:
                    # 博主访问自己的博客
                    author_topics = Topic.objects.filter(author_id=author_id)
                else:
                    author_topics = Topic.objects.filter(author_id=author_id, limit='public')
            res = self.make_topics_res(author, author_topics)
            return JsonResponse(res)


    @method_decorator(logging_check)
    def delete(self, request, author_id):
        # 首先拿到要删除的博客id：t_id,查库删除即可
        t_id = request.GET.get('t_id')
        # print(t_id)
        try:
            topic = Topic.objects.get(id=t_id)
        except Exception as e:
            return JsonResponse({'code': 10310, 'error': 'This topic is not existed'})
        # topic = get_object_or_404(Topic, pk=t_id)
        topic.delete()
        # 删除缓存
        self.clear_topics_caches(request)
        return JsonResponse({'code': 200})
