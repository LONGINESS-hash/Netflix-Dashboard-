import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px

from PIL import Image

try:
    icon = Image.open('images.png')
except FileNotFoundError:
    icon = '🎬'

st.set_page_config(
    page_title="Netflix Database Dashboard",
    page_icon=icon,
    layout="wide",
    initial_sidebar_state="expanded")
alt.themes.enable("dark")

#load the csv file provided
@st.cache_data
def load_data():
    data = pd.read_csv('netflix_titles.csv')
    #turn the date into the right format
    data['year_added'] = pd.to_datetime(data['date_added'].str.strip(), errors='coerce').dt.year
    return data

df = load_data()

#add a bit of UI

st.markdown("""
<style>
[data-testid="block-container"] {
    padding-left: 2rem;
    padding-right: 2rem;
    padding-top: 1rem;
    padding-bottom: 0rem;
    margin-bottom: -7rem;
}
[data-testid="stVerticalBlock"] {
    padding-left: 0rem;
    padding-right: 0rem;
}
[data-testid="stMetric"] {
    background-color: #393939;
    text-align: center;
    padding: 15px 0;
}
[data-testid="stMetricLabel"] {
  display: flex;
  justify-content: center;
  align-items: center;
}
[data-testid="stMetricDeltaIcon-Up"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}
[data-testid="stMetricDeltaIcon-Down"] {
    position: relative;
    left: 38%;
    -webkit-transform: translateX(-50%);
    -ms-transform: translateX(-50%);
    transform: translateX(-50%);
}
</style>
""", unsafe_allow_html=True)

#create the side menu dropdown
with st.sidebar:
  st.title('Netflix Dashboard')

  year_list = sorted(df['year_added'].dropna().astype(int).unique(), reverse=True)

  selected_year = st.selectbox('Select a Year', year_list, index=0)
  df_selected_year = df[df['year_added'] == selected_year]
  df_selected_year_sorted = df_selected_year.sort_values(by="release_year", ascending=False)
  color_theme_list = ['blues', 'cividis', 'greens', 'inferno', 'magma', 'plasma', 'reds', 'rainbow', 'turbo', 'viridis' ]
  selected_color_theme = st.selectbox('Select a color theme', color_theme_list)
  genre_list = sorted(df['listed_in'].str.split(', ').explode().str.strip(' ,').unique())
  selected_genre = st.selectbox('Select a genre', genre_list)

def make_donut(input_response, input_text, input_color):
  if input_color == 'blue':
      chart_color = ['#29b5e8', '#155F7A']
  if input_color == 'green':
      chart_color = ['#27AE60', '#12783D']
  if input_color == 'orange':
      chart_color = ['#F39C12', '#875A12']
  if input_color == 'red':
      chart_color = ['#E74C3C', '#781F16']

  source = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100-input_response, input_response]
  })
  source_bg = pd.DataFrame({
      "Topic": ['', input_text],
      "% value": [100, 0]
  })

  plot = alt.Chart(source).mark_arc(innerRadius=45, cornerRadius=25).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          #domain=['A', 'B'],
                          domain=[input_text, ''],
                          # range=['#29b5e8', '#155F7A']),  # 31333F
                          range=chart_color),
                      legend=None),
  ).properties(width=130, height=130)

  text = plot.mark_text(align='center', color="#29b5e8", font="Lato", fontSize=32, fontWeight=700, fontStyle="italic").encode(text=alt.value(f'{input_response} %'))
  plot_bg = alt.Chart(source_bg).mark_arc(innerRadius=45, cornerRadius=20).encode(
      theta="% value",
      color= alt.Color("Topic:N",
                      scale=alt.Scale(
                          # domain=['A', 'B'],
                          domain=[input_text, ''],
                          range=chart_color),  # 31333F
                      legend=None),
  ).properties(width=130, height=130)
  return plot_bg + plot + text

#top 4 movie genres (donut charts)

movies = df[df['type'] == 'Movie']
genre_counts = movies['listed_in'].str.split(', ').explode().value_counts().head(4)

colors = ['blue', 'green', 'orange', 'red']
cols = st.columns(4)

for col, (genre, count), color in zip(cols, genre_counts.items(), colors):
    pct = int(round(count / len(movies) * 100))
    with col:
        st.markdown(f'#### :{color}[{genre}]')
        st.altair_chart(make_donut(pct, genre, color))
        st.metric(label='Movies', value=f'{count:,}')

col = st.columns((1.5, 4.5, 2), gap='medium')


def calculate_genre_difference(df, selected_year):
    exploded = df.assign(genre=df['listed_in'].str.split(', ')).explode('genre')
    current = exploded[exploded['year_added'] == selected_year]['genre'].value_counts()
    previous = exploded[exploded['year_added'] == selected_year - 1]['genre'].value_counts()
    result = pd.DataFrame({'titles': current, 'previous': previous}).fillna(0)
    result['difference'] = result['titles'] - result['previous']
    return result.reset_index(names='genre').sort_values('difference', ascending=False)

#start with the columns
 
with col[0]:
    st.markdown('#### Gains/Losses')
    df_genre_difference_sorted = calculate_genre_difference(df, selected_year)

    if selected_year > df['year_added'].min():
        first_genre_name = df_genre_difference_sorted.genre.iloc[0]
        first_genre_titles = int(df_genre_difference_sorted.titles.iloc[0])
        first_genre_delta = int(df_genre_difference_sorted.difference.iloc[0])
    else:
        first_genre_name = '-'
        first_genre_titles = '-'
        first_genre_delta = ''
    st.metric(label=first_genre_name, value=first_genre_titles, delta=first_genre_delta)

    if selected_year > df['year_added'].min():
        last_genre_name = df_genre_difference_sorted.genre.iloc[-1]
        last_genre_titles = int(df_genre_difference_sorted.titles.iloc[-1])
        last_genre_delta = int(df_genre_difference_sorted.difference.iloc[-1])
    else:
        last_genre_name = '-'
        last_genre_titles = '-'
        last_genre_delta = ''
    st.metric(label=last_genre_name, value=last_genre_titles, delta=last_genre_delta)

    st.markdown('#### Genre Trend')
    if selected_year > df['year_added'].min():
        df_up = df_genre_difference_sorted[df_genre_difference_sorted.difference > 0]
        df_down = df_genre_difference_sorted[df_genre_difference_sorted.difference < 0]
        genres_up = round(len(df_up) / df_genre_difference_sorted.genre.nunique() * 100)
        genres_down = round(len(df_down) / df_genre_difference_sorted.genre.nunique() * 100)
    else:
        genres_up = 0
        genres_down = 0

    donut_chart_up = make_donut(genres_up, 'Growing Genres', 'green')
    donut_chart_down = make_donut(genres_down, 'Shrinking Genres', 'red')

    trend_col = st.columns((0.2, 1, 0.2))
    with trend_col[1]:
        st.write('Growing')
        st.altair_chart(donut_chart_up)
        st.write('Shrinking')
        st.altair_chart(donut_chart_down)

#map of the world with genre by country

with col[1]:
    st.markdown(f'#### {selected_genre} around the world')

    genre_df = (df.assign(genre=df['listed_in'].str.split(', '),
                          country=df['country'].str.split(', '))
                  .explode('genre'))
    genre_df['genre'] = genre_df['genre'].str.strip(' ,')
    genre_df = genre_df[genre_df['genre'] == selected_genre].explode('country')
    genre_df['country'] = genre_df['country'].str.strip(' ,')

    country_counts = genre_df['country'].replace('', pd.NA).dropna().value_counts().reset_index()
    country_counts.columns = ['country', 'titles']

    fig = px.choropleth(country_counts,
                        locations='country',
                        locationmode='country names',
                        color='titles',
                        color_continuous_scale=selected_color_theme)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=400)
    st.plotly_chart(fig, width='stretch')

    #Movies vs TV Shows added per year
    st.markdown('#### Movies vs TV Shows added per year')
    df_dated = df.dropna(subset=['year_added'])
    type_by_year = pd.crosstab(df_dated['year_added'].astype(int), df_dated['type'])
    st.bar_chart(type_by_year, color=['#E74C3C', '#29b5e8'], x_label='Year', y_label='Titles added')

#now a datafram with countries and movies produced
with col[2]:
    st.markdown(f'#### Top Countries: {selected_genre}')
    st.dataframe(country_counts,
                 column_order=("country", "titles"),
                 hide_index=True,
                 width='stretch',
                 column_config={
                    "country": st.column_config.TextColumn(
                        "Country",
                    ),
                    "titles": st.column_config.ProgressColumn(
                        "Titles",
                        format="%d",
                        min_value=0,
                        max_value=int(country_counts.titles.max()),
                     )}
                 )

    pct_no_director = round(df['director'].isnull().mean() * 100)
    pct_no_country = round(df['country'].isnull().mean() * 100)

    
    with st.expander('About', expanded=False):
        st.write(f'''
            - Data: Netflix titles dataset (netflix_titles.csv).
            - :orange[**Gains/Losses**]: genres with the biggest increase/decrease in titles added vs. the previous year
            - :orange[**Genre Trend**]: percentage of genres that grew/shrank in titles added vs. the previous year
            - :orange[**Map and Top Countries**]: number of titles per country for the selected genre
            - :orange[**Movies vs TV Shows**]: how many movies and TV shows were added each year
            ''')

    with st.expander('Data limits', expanded=False):
        st.write(f'''
            - 2021 is a partial year (data ends Sept 25, 2021), so it can look like a decline.
            - 2008-2014 have fewer than 25 titles added per year, so their Gains/Losses are mostly noise.
            - {pct_no_country}% of titles have no country, so the map undercounts. {pct_no_director}% have no director.
            ''')
