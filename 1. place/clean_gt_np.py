
# coding: utf-8

# In[30]:

import pandas as pd
import math
data = '../data/place_np_statisic_raw.csv'
df = pd.read_csv(data)


# In[32]:

df.dropna(how='all',inplace=True)
df['place'] = df['place'].fillna(method='ffill')


# In[33]:

df.drop(u'Unnamed: 14',axis=1, inplace=True)


# In[34]:

clean_df = pd.melt(df,id_vars=['place','Year'],var_name='month', value_name='gt_visit')


# In[35]:

clean_df.Year = clean_df.Year.apply(lambda x: x.replace(',',''))


# In[38]:

clean_df.gt_visit = clean_df.gt_visit.apply(lambda x: x.replace(',','') if type(x)==str else x)


# In[39]:

clean_df.place = clean_df.place.apply(lambda x: x.replace(' ','_'))


# In[40]:

', '.join(clean_df.month.value_counts().index.tolist())


# In[41]:

standardized_month = {
    'Jan':'01', 'Feb':'02', 'March':'03', 'April':'04', 'May':'05', 'June':'06', 'July':'07', 'August':'08',
    'September':'09', 'October':'10', 'November':'11', 'December':'12'
}
clean_df.month = clean_df.month.apply(lambda x: standardized_month[x])


# In[42]:

clean_df['ym'] = clean_df.apply(lambda x: '%s_%s' % (x.Year, x.month),axis=1)


# In[44]:

clean_df.dropna(inplace=True)


# In[45]:

clean_df.to_csv('../data/place_np_statisic_clean.csv')


# In[ ]:



