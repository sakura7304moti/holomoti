#!/usr/bin/env python
# coding: utf-8

# In[1]:


#get_ipython().system('uv pip list')


# ## ホロメンの一覧取得

# In[2]:


import pandas as pd
import time
import requests
import urllib
import datetime


from sqlalchemy import create_engine
from tqdm import tqdm

from module import utils # 自作モジュール


# ## ツイート取得処理

# In[3]:


# 実際に使うセル

def parse_date(epoch_seconds:int):
    """
    エポック時間をyyyy-mm-ddに変換
    """
    dt = datetime.datetime.utcfromtimestamp(epoch_seconds)
    formatted_date = dt.strftime('%Y-%m-%d')
    return formatted_date


def get_pagination_url(hashtag:str , last_tweet_id=''):
    """
    ハッシュタグと最後のツイートIDを元にツイートを取得
    """
    hashtag_encode = urllib.parse.quote(hashtag)
    base = 'https://search.yahoo.co.jp/realtime/api/v1/pagination?crumb=mAPCZQAAAADNdZd0dcgpPQgDqP92PnuPEMSk6lxd4YGq8c2mRAgBCM2UUYvzIQxomlV2QJ6ctst25ElZTfbJIAemJT7h8JGy'
    url = f'{base}&p={hashtag_encode}&rkf=3&b=1&mtype=image'
    if last_tweet_id != '':
        return url + f'&oldestTweetId={last_tweet_id}&start='
    else:
        return url
    
def add_ok(row:dict):
    #return True
    return row['likesCount'] > 10 and 'media' in row

def get_tweets(res:dict):
    tweets = []
    for row in res.json()['timeline']['entry']:
        tweet = {
            'id' : int(row['id']),
            'tweet_text': row['displayText'],
            'tweet_url': row['url'],
            'like_count':row['likesCount'],
            'user_screen_name':row['screenName'],
            'created_at':row['createdAt']
        }
        #likecountとmediaの存在チェックをした上で追加する
        if add_ok(row):
            tweets.append(tweet)
    return tweets

def get_medias(res:dict):
    medias = []
    for row in res.json()['timeline']['entry']:
        if 'media' not in row:
            continue
        tweet_id = int(row['id'])
        for m in row['media']:
            media = {
                'twitter_id':tweet_id,
                'media_type':m['type'],
                'media_url':m['item']['mediaUrl'],
                'thumbnail_url':m['item']['thumbnailImageUrl']
            }
            if add_ok(row):
                medias.append(media)
    return medias

def get_hashtags(res:dict):
    hashtags = []
    for row in res.json()['timeline']['entry']:
        tweet_id = int(row['id'])
        for item in [h['text'] for h in row['hashtags']]:
            tag = {
                'twitter_id':tweet_id,
                'hashtag':item
            }
            if add_ok(row):
                hashtags.append(tag)
    return hashtags

def get_users(res:dict):
    users = []
    for row in res.json()['timeline']['entry']:
        user = {
            'screen_name':row['screenName'],
            'updated_at':row['createdAt'],
            'name':row['name'],
            'profile_image':row['profileImage']
        }
        #likecountとmediaの存在チェックをした上で追加する
        if add_ok(row):
            users.append(user)
    return users

def get_list(url:str):
    """
    URLを元にツイートのリストを取得
    """
    time.sleep(0.5)
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"response status_code -> {response.status_code} {response}")
    records_dict = {
        'tweet':get_tweets(response),
        'media':get_medias(response),
        'hashtag':get_hashtags(response),
        'user':get_users(response)
    }

    if len(response.json()['timeline']['entry']) == 0:
        last_tweet_id = ''
        last_date = datetime.datetime.now().date()
    else:
        last_tweet_id = response.json()['timeline']['entry'][-1]['id']
        last_date = datetime.datetime.fromtimestamp(response.json()['timeline']['entry'][-1]['createdAt'],tz=datetime.timezone.utc).date()
    return records_dict , last_tweet_id , last_date

def date_difference(specified_date):
    """
    今日の日付と引数のyyyy-mm-ddを比較して、日数差を返す
    """
    today = datetime.datetime.now().date()
    difference = abs((today - specified_date).days)
    return difference

def get_tweet(hashtag:str , date:int ):
    """
    ツイートを取得する
    """
    tweets = []
    medias = []
    hashtags = []
    users = []

    first_url = get_pagination_url(hashtag)
    records_dict , last_tweet_id , last_date = get_list(first_url)
    tweets.extend(records_dict['tweet'])
    medias.extend(records_dict['media'])
    hashtags.extend(records_dict['hashtag'])
    users.extend(records_dict['user'])
    
    while(True):
        url = get_pagination_url(hashtag , last_tweet_id)
        records_dict , last_tweet_id , last_date = get_list(url)
        tweets.extend(records_dict['tweet'])
        medias.extend(records_dict['media'])
        hashtags.extend(records_dict['hashtag'])
        users.extend(records_dict['user'])

        # 追加処理
        if last_tweet_id == '':
            break
        if date_difference(last_date) > date:
            break

    result = {
        'tweet':tweets,
        'media':medias,
        'hashtag':hashtags,
        'user':users
    }
    return result


def tweet_to_sql(records_dict:dict):
    model = utils.PsqlBase()
    df = pd.DataFrame(records_dict['tweet'])

    # 日付を日本時間に
    df['created_at'] = pd.to_datetime(df['created_at'], unit='s')
    df['created_at'] = df['created_at'].dt.tz_localize('UTC')
    df['created_at'] = df['created_at'].dt.tz_convert('Asia/Tokyo')

    # データフレームをテーブルに
    df.to_sql(
        name='twitter_tweet_tmp',
        con=model.db_pd_connection(),
        schema='holo',
        if_exists='replace',
        index=False,
        method='multi'
    )

    # 更新クエリ
    update_query = """
        WITH us as(
            SELECT
                id,
                tweet_text,
                tweet_url,
                like_count,
                user_screen_name,
                created_at
            FROM
                holo.twitter_tweet_tmp AS tmp
            WHERE
                tmp.id IN (
                    SELECT
                        u.id
                    FROM
                        holo.twitter_tweet AS u
                )
        )
        update holo.twitter_tweet as u
        SET
            like_count = us.like_count
        from us
        where u.id = us.id
    """
    model.execute_commit(update_query)

    # 追加クエリ
    insert_query = """
        INSERT INTO
        holo.twitter_tweet AS us
        (
            id,
            tweet_text,
            tweet_url,
            like_count,
            user_screen_name,
            created_at
        )
        SELECT
            id,
            tweet_text,
            tweet_url,
            like_count,
            user_screen_name,
            created_at
        FROM
            holo.twitter_tweet_tmp AS tmp
        WHERE
            tmp.id not IN (
                SELECT
                    u.id
                FROM
                    holo.twitter_tweet AS u
            )
    """
    model.execute_commit(insert_query)
    return df


# In[7]:


#tweet_to_sql(records_dict)


# ## ハッシュタグをテーブルに保存

# In[8]:


def hashtag_to_sql(records_dict:dict):
    model = utils.PsqlBase()
    df = pd.DataFrame(records_dict['hashtag'])
    
    # データフレームをテーブルに
    df.to_sql(
        name='twitter_hashtag_tmp',
        con=model.db_pd_connection(),
        schema='holo',
        if_exists='replace',
        index=False,
        method='multi'
    )

    # 追加クエリ
    insert_query = """
        INSERT INTO
        holo.twitter_hashtag AS us
        (
            twitter_id,
            hashtag
        )
        SELECT
            tmp.twitter_id,
            tmp.hashtag
        FROM
            holo.twitter_hashtag_tmp AS tmp
        left join holo.twitter_hashtag as u 
        on tmp.twitter_id = u.twitter_id and tmp.hashtag = u.hashtag
        where u.twitter_id IS NULL AND u.hashtag IS NULL
    """
    model.execute_commit(insert_query)
    return df


# In[9]:


#hashtag_to_sql(records_dict)


# ## メディアをテーブルに保存

# In[10]:


def media_to_sql(records_dict:dict):
    model = utils.PsqlBase()
    df = pd.DataFrame(records_dict['media'])

    df.to_sql(
        name='twitter_media_tmp',
        con=model.db_pd_connection(),
        schema='holo',
        if_exists='replace',
        index=False,
        method='multi'
    )

    insert_query = """
    INSERT INTO
    holo.twitter_media AS us
    (
        twitter_id,
        media_type,
        media_url,
        thumbnail_url
    )
    SELECT
        tmp.twitter_id,
        tmp.media_type,
        tmp.media_url,
        tmp.thumbnail_url
    FROM
        holo.twitter_media_tmp AS tmp
    left join holo.twitter_media as u 
    on 
        tmp.twitter_id = u.twitter_id 
        and tmp.media_type = u.media_type
        and tmp.media_url = u.media_url
        and tmp.thumbnail_url = u.thumbnail_url
    where 
        u.twitter_id IS NULL
        AND u.media_type IS NULL
        AND u.media_url IS NULL
        AND u.thumbnail_url IS NULL
    """
    model.execute_commit(insert_query)
    return df


# In[11]:


#media_to_sql(records_dict)


# ## ユーザーをテーブルに保存

# In[12]:


def user_to_sql(records_dict:dict):
    model = utils.PsqlBase()
    df = pd.DataFrame(records_dict['user'])
    # 日付を日本時間に
    df['updated_at'] = pd.to_datetime(df['updated_at'], unit='s')
    df['updated_at'] = df['updated_at'].dt.tz_localize('UTC')
    df['updated_at'] = df['updated_at'].dt.tz_convert('Asia/Tokyo')
    
    # 一時保存用のユーザーテーブルを作成する
    df.to_sql(
        name='twitter_user_tmp',
        con=model.db_pd_connection(),
        schema='holo',
        if_exists='replace',
        index=False,
        method='multi'
    )

    # 更新クエリ
    update_query = """
        WITH us as(
            SELECT
                tmp.screen_name,
                max(tmp.name) as name,
                max(tmp.profile_image) as profile_image,
                max(tmp.updated_at) as updated_at
            FROM
                holo.twitter_user_tmp AS tmp
            WHERE
                tmp.screen_name IN (
                    SELECT
                        u.screen_name
                    FROM
                        holo.twitter_user AS u
                    WHERE 
                        u.screen_name = tmp.screen_name
                        and tmp.updated_at > u.updated_at
                )
            group by tmp.screen_name
        )
        update holo.twitter_user as u
        SET
            name = us.name,
            profile_image = us.profile_image,
            updated_at = us.updated_at
        from us
        where u.screen_name = us.screen_name
    """
    model.execute_commit(update_query)

    # 追加クエリ
    insert_query = """
        INSERT INTO
            holo.twitter_user AS us
        (
            screen_name,
            name,
            profile_image,
            updated_at
        )
        SELECT
            tmp.screen_name,
            max(tmp.name),
            max(tmp.profile_image),
            max(tmp.updated_at)
        FROM
            holo.twitter_user_tmp AS tmp
        WHERE
            tmp.screen_name not IN (
                SELECT
                    u.screen_name
                FROM
                    holo.twitter_user AS u
            )
        group by tmp.screen_name
    """
    model.execute_commit(insert_query)


# In[13]:


#user_to_sql(records_dict)


# ## 本番想定！

# In[14]:

def main():
    opt = utils.Option()
    holonames = pd.read_csv(opt.holo_names())
    hashtags = holonames['hashtag'].drop_duplicates().tolist()
    for tag in tqdm(hashtags):
        print(f"\r tag : {tag}",end="")
        # データの取得
        records_dict = get_tweet(tag,365*10)

        # データの存在チェック
        if len(records_dict['tweet']) > 0:
            # データの更新
            tweet_to_sql(records_dict)
            hashtag_to_sql(records_dict)
            media_to_sql(records_dict)
            user_to_sql(records_dict)

