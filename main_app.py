import streamlit as st
import numpy as np
import pandas as pd
import plotly.express as px
pd.options.mode.chained_assignment = None
import warnings
warnings.filterwarnings('ignore')

user_name_0_color = '#87c6d7'
user_name_1_color = '#FFB6C1'

def get_granularity(granularity_filter):
    if granularity_filter == "День":
        return 'day_date'
    elif granularity_filter == "Неделя":
        return 'week_date'
    elif granularity_filter == "Месяц":
        return 'month_date'
    elif granularity_filter == "Год":
        return 'year_date'
    return 'month_date'

# Интерфейс загрузки файла
st.title("Telegram Analyze")
uploaded_file = st.file_uploader("Загрузите вашу переписку в формате .json", type=["json"])

# Инструкция для пользователя
with st.expander("Как выгрузить данные?"):
    st.write("""
    1. Зайдите в переписку с собеседником, которую вы хотите проанализировать.
    2. Нажмите на 3 точки в правом верхнем углу.
    """)
    st.image("https://i.postimg.cc/Y9HxrxyN/first-screen.png")
    st.write("""
    3. Перейдите к Экспорту истории чата.
    """)
    st.image("https://i.postimg.cc/mhfLJtrr/second-screen.png")
    st.write("""
    4. В настройках экспорта уберите галочки со всех пунктов. В формате выберите "Машиночитаемый JSON".
    """)
    st.image("https://i.postimg.cc/jd7Q7m06/third-screen.png")
    st.write(r"""
    5. Подождите скачивание файла. Прогресс скачивания будет отображаться в Telegram.
    6. Если вы не меняли стандартный путь к файлу, то он должен скачаться в Telegram Desktop. Поищите его в C:\Users\\<ВАШ ЮЗЕР>\\Downloads\\Telegram Desktop\\ChatExport_<ДАТА ЭКСПОРТА>.
    """)
    st.image("https://i.postimg.cc/HsXvgVxC/image.png")
    st.write("""
    7. Готово✅ Теперь загрузите файл в формулу выше👆
    """)

if uploaded_file:
    # Чтение данных
    df_json = pd.read_json(uploaded_file)
    df = pd.json_normalize(df_json['messages'])

    # Обработка данных
    df['date'] = pd.to_datetime(df['date'])
    df['hour_date'] = df['date'].dt.hour
    df['day_date'] = df['date'].dt.to_period('D').dt.to_timestamp()
    df['week_date'] = df['date'].dt.to_period('W').dt.to_timestamp()
    df['month_date'] = df['date'].dt.to_period('M').dt.to_timestamp()
    df['year_date'] = df['date'].dt.to_period('Y').dt.to_timestamp()
    df['day_of_week'] = df['date'].dt.day_name(locale='ru_RU')
    df['day_of_month'] = df['date'].dt.day
    df['message_length'] = df['text'].apply(len)

    df_info = df[['id', 'date', 'from', 'text', 'hour_date', 'day_date', 'week_date', 'month_date', 'year_date', 'day_of_week', 'day_of_month', 'message_length']]

    # Заголовок анализа
    user_names = df_info['from'].dropna().unique()
    user_name_0_colored = f'<span style="color: {user_name_0_color};">{user_names[0]}</span>'
    user_name_1_colored = f'<span style="color: {user_name_1_color};">{user_names[1]}</span>'
    if len(user_names) >= 2:
        st.markdown(
            f'<h3>Анализ переписки между {user_name_0_colored} и {user_name_1_colored}</h3>',
            unsafe_allow_html=True
        )
    else:
        st.subheader("Анализ переписки")

    # Боковая панель фильтров
    st.sidebar.header("Фильтры")
    start_date = st.sidebar.date_input("Начальная дата", value=df_info['date'].min().date())
    end_date = st.sidebar.date_input("Конечная дата", value=df_info['date'].max().date())
    granularity_filter = st.sidebar.selectbox("Гранулярность", ["День", "Неделя", "Месяц", "Год"])
    granularity = get_granularity(granularity_filter=granularity_filter)
    filter_message = st.sidebar.text_input("Поиск по сообщениям")

    # Применение фильтров
    filtered_df = df_info[(df_info['date'] >= pd.Timestamp(start_date)) &
                          (df_info['date'] <= pd.Timestamp(end_date)) &
                          (df_info['text'].str.contains(filter_message, case=False, na=False))]

    # Визуализация 1: Стековая гистограмма
    grouped = filtered_df.groupby([granularity, 'from']).size().reset_index(name='count')
    fig = px.bar(grouped, x=granularity, y='count', color='from',
                 title="График распределения сообщений по гранулярности",
                 labels={granularity: granularity_filter, 'count': "Количество сообщений", 'from' : "Пользователь"},
                 color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    st.plotly_chart(fig, use_container_width=True)

    # Визуализация 2: Печенька
    message_counts = filtered_df['from'].value_counts()
    pie_fig = px.pie(names=message_counts.index, values=message_counts.values,
                     title="Распределение сообщений",
                     labels={'from' : "Пользователь"},
                     color=message_counts.index,
                     color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    st.plotly_chart(pie_fig, use_container_width=False)

    # Визуализация 3: Распределение по часам
    hourly_counts = filtered_df.groupby(['hour_date', 'from']).size().reset_index(name='count')
    hour_fig = px.bar(hourly_counts, x='hour_date', y='count', color='from',
                      title="График распределения сообщений по часам",
                      labels={'hour_date': "Час отправки", 'count': "Количество сообщений", 'from' : "Пользователь"},
                      color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    hour_fig.update_layout(
        annotations=[
            dict(
                text="Указано ваше локальное время.",
                xref="paper", yref="paper",
                x=0, y=1.05,  # Позиция над графиком
                showarrow=False,
                font=dict(size=12, color="gray")
            )
        ]
    )
    st.plotly_chart(hour_fig, use_container_width=True)

    # Визуализация 4: Распределение по дням месяца
    daily_counts = filtered_df.groupby(['day_of_month', 'from']).size().reset_index(name='count')
    day_fig = px.bar(daily_counts, x='day_of_month', y='count', color='from',
                     title="График распределения сообщений по дням месяца",
                     labels={'day_of_month': "День месяца", 'count': "Количество сообщений", 'from' : "Пользователь"},
                     color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    st.plotly_chart(day_fig, use_container_width=True)

    # Визуализация 5: Распределение по дням недели
    weekly_counts = filtered_df.groupby(['day_of_week', 'from']).size().reset_index(name='count')
    week_fig = px.bar(weekly_counts, x='day_of_week', y='count', color='from',
                       title="График распределения сообщений по дням недели",
                       labels={'day_of_week': "День недели", 'count': "Количество сообщений", 'from' : "Пользователь"},
                       category_orders={"day_of_week": ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]},
                       color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    st.plotly_chart(week_fig, use_container_width=True)

    # Визуализация 6: Топ-5 дней с наибольшим количеством сообщений
    daily_totals = filtered_df.groupby(['day_date', 'from']).size().reset_index(name='count_messages')
    daily_totals_sum = daily_totals.groupby(['day_date'], as_index=False).agg(all_messages=('count_messages', 'sum'))
    daily_totals_sum = daily_totals_sum.merge(daily_totals, on='day_date', how='inner')
    top_5_days = daily_totals_sum.groupby('day_date')['all_messages'].sum().nlargest(5).index
    daily_totals_filtered = daily_totals_sum[daily_totals_sum['day_date'].isin(top_5_days)]
    daily_totals_filtered = daily_totals_filtered.sort_values(['all_messages'])

    daily_totals_filtered['day_date'] = daily_totals_filtered['day_date'].dt.strftime('%d.%m.%Y')
    top_fig = px.bar(daily_totals_filtered, y='day_date', x='count_messages', color='from',
                     title="Топ-5 дней с наибольшим количеством сообщений",
                     labels={'day_date': "Дата", 'count_messages': "Количество сообщений", 'from' : "Пользователь"},
                     color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})
    st.plotly_chart(top_fig, use_container_width=True)

    # Визуализация 7: Динамика накопленных часов, потраченных на переписку
    daily_stats = filtered_df.groupby(granularity).agg(
        median_message_length=('message_length', 'median'),
        message_count=('message_length', 'size')
    ).reset_index()

    daily_stats['total_hours_spent'] = (daily_stats['median_message_length'] * daily_stats['message_count']) / 120 / 60
    daily_stats['total_hours_spent_cumulative'] = daily_stats['total_hours_spent'].cumsum()
    daily_stats['total_hours_spent_cumulative'] = np.round(daily_stats['total_hours_spent_cumulative'], 2)

    cumsum_hours_fig = px.line(daily_stats, x=granularity, y='total_hours_spent_cumulative',
                title='Динамика накопленных часов, потраченных на переписку',
                labels={granularity: granularity_filter, 'total_hours_spent_cumulative': 'Накопленные часы'})
    st.plotly_chart(cumsum_hours_fig, use_container_width=True)
    st.success(f"Всего потрачено на переписку: ~{daily_stats['total_hours_spent_cumulative'].max()} ч.")
    st.caption("Подсчитано с учетом фильтра на календарные даты и поиска по сообщениям.")

    # Визуализация 8: Среднее время ответа пользователями
    df_info = df_info.tail(10000)

    # Инициализация столбцов
    df_info['time_to_next_response'] = None
    df_info['time_since_last_from_other'] = None
    df_info['other_user'] = None

    # Словарь для отслеживания последнего сообщения от каждого пользователя
    last_message_from = {}

    # Обрабатываем каждое сообщение
    for i in range(len(df_info)):
        current_message = df_info.iloc[i]
        current_user = current_message['from']
        current_date = current_message['date']
        
        # Находим собеседников (все, кроме текущего пользователя)
        other_users = df_info['from'].unique().tolist()
        other_users.remove(current_user)
        
        # Находим последнее сообщение от любого другого пользователя
        last_other_message = None
        for user in other_users:
            if user in last_message_from:
                candidate_message = last_message_from[user]
                if (last_other_message is None) or (candidate_message['date'] > last_other_message['date']):
                    last_other_message = candidate_message
        
        # Проверяем, прошло ли больше часа с последнего сообщения от собеседника
        if last_other_message is not None:
            time_diff = (current_date - last_other_message['date']).total_seconds()
            df_info['time_since_last_from_other'].iloc[i] = time_diff

            if time_diff >= 1800:
                # Ищем следующее сообщение от собеседника
                next_response_time = None
                for j in range(i+1, len(df_info)):
                    if df_info.iloc[j]['from'] != current_user:
                        next_response_time = (df_info.iloc[j]['date'] - current_date).total_seconds()
                        other_user = df_info.iloc[j]['from']
                        break
                df_info['time_to_next_response'].iloc[i] = next_response_time
                df_info['other_user'].iloc[i] = other_user

        # Обновляем последнее сообщение от текущего пользователя
        last_message_from[current_user] = current_message

    # Переводим время ответа в минуты
    df_info['time_to_next_response'] /= 60  # Минуты

    # Группируем по дням и other_user, считаем медиану
    daily_median = df_info.groupby(['day_date', 'other_user'])['time_to_next_response'].median().reset_index()

    # Рассчитываем накопительную медиану (по медиане всех предыдущих дней)
    daily_median['cumulative_median'] = daily_median.groupby('other_user')['time_to_next_response'].expanding().median().reset_index(level=0, drop=True)

    # Определяем дату 10000-го сообщения
    df_info = df_info.sort_values(by='date', ascending=False)
    df_info['cumulative_messages'] = range(1, len(df_info) + 1)
    if len(df_info) >= 10000:
        date_10000th_message = df_info.iloc[9999]['date']
    else:
        date_10000th_message = df_info.iloc[-1]['date']

    # Вычисляем среднее время ответа после даты 10000-го сообщения
    df_after_10000 = df_info[df_info['date'] >= date_10000th_message]

    # Общее медианное значение по other_user
    overall_median_response = df_info.groupby('other_user')['time_to_next_response'].median()

    overall_median_response_df = pd.DataFrame({
        'user' : [overall_median_response.index[0], overall_median_response.index[1]],
        'value' : [overall_median_response.values[0], overall_median_response.values[1]]
    })

    # Создание гистограммы
    fig_overall_median_response = px.bar(overall_median_response_df, x="user", y="value", text="value", color="user",
                title=f"Среднее время ответа пользователями с момента {date_10000th_message.strftime('%d.%m.%Y')}",
                labels={"user": "Пользователь", "value": "Минуты"},
                #color="user",
                color_discrete_map={user_names[0]: user_name_0_color, user_names[1]: user_name_1_color})

    fig_overall_median_response.update_traces(textposition="outside")  # Числовые значения на столбцах
    st.plotly_chart(fig_overall_median_response, use_container_width=True)
