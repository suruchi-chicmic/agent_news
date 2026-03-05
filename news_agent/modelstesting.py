# from google import genai

# client = genai.Client(api_key="AIzaSyBaeJj5pUrIXMA5zNjqE59DLA4RHioD_Q4")

# models = client.models.list()
# for m in models:
#     print(m.name)

from newsapi import NewsApiClient

# Init
newsapi = NewsApiClient(api_key='dcdcbbb959584b8f9f91d0fb1021d45e')

# /v2/top-headlines
top_headlines = newsapi.get_top_headlines(q='AI',
                                        #   category='Technology',
                                          language='en')
                                        #   country='us')

print(top_headlines)

# /v2/everything
# all_articles = newsapi.get_everything(q='bitcoin',
#                                       sources='bbc-news,the-verge',
#                                       domains='bbc.co.uk,techcrunch.com',
#                                       from_param='2017-12-01',
#                                       to='2017-12-12',
#                                       language='en',
#                                       sort_by='relevancy',
#                                       page=2)

# /v2/top-headlines/sources
# sources = newsapi.get_sources()

