import math

from django.shortcuts import render, redirect
from .forms import *
from .models import *
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np


def upload_file(request):
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            if Statistic.objects.all():
                return redirect('statistics')
            pd.set_option('display.max_columns', None)
            statistics = pd.read_excel(request.FILES['file']).iloc[:, 1:7].drop(['trbc_code_description', 'trbc_code'],
                                                                                axis=1).rename(
                {'year (FiscalYear)': 'year', 'Total Operating Expense (ETOE)': 'expense',
                 'Operating Income (SOPI)': 'income', "Company ('Type': 'CompanyName', 'Value':)": 'name'}, axis=1)
            for statistic in statistics.itertuples():
                Statistic.objects.create(name=statistic.name, date=statistic.year, expense=statistic.expense,
                                         income=statistic.income)
            return redirect('statistics')
    else:
        form = UploadForm()
    return render(request, 'app/file_upload.html', {'form': form})


def statistics(request):
    stats = Statistic.objects.all().order_by('date')
    investments = {}
    show_graph = False
    if not stats:
        return redirect('upload_file')
    if request.method == 'POST':
        form = BCoeffForm(request.POST)
        if form.is_valid():
            b = form.cleaned_data['b']
            graph_data = {}
            for stat in stats:
                if stat.name not in graph_data:
                    graph_data[stat.name] = [(stat.expense, stat.income)]
                else:
                    graph_data[stat.name].append((stat.expense, stat.income))
            plt.figure().clear()
            for company in graph_data:
                graph_data[company] = sorted(graph_data[company], key=lambda item: item[0])
                y_max = max([item[1] for item in graph_data[company]])
                y_min = min([item[1] for item in graph_data[company]])
                x_max = graph_data[company][-1][0]
                x_min = graph_data[company][0][0]
                try:
                    a = math.log10((y_max / y_min * (10 ** (-b * x_min) - 1) / (10 ** (-b * x_max) - 1) - 1) / (
                            10 ** (-b * x_min) - 10 ** (-b * x_max) * y_max / y_min * (10 ** (-b * x_min) - 1) / (
                            10 ** (-b * x_max) - 1)))
                    A = y_max * (1 + 10 ** a) / 10 ** a * (1 + 10 ** (a - b * x_max) / (1 - 10 ** (-b * x_max)))
                except:
                    continue
                y_data = []
                x_data = np.linspace(0, x_max * 1.5, 500)
                for x in x_data:
                    y_data.append(
                        (A * 10 ** a) / (1 + 10 ** a) * (1 - 10 ** (-b * x)) / (1 + 10 ** (a - b * x)))
                y_max = 0
                max_index = 0
                for i, y in enumerate(y_data):
                    if y >= y_max:
                        y_max = y
                        max_index = i
                if x_data[max_index] == y_max:
                    investments[company] = 'Кампания не подаёт признаков роста или уменьшения'
                elif x_data[max_index] > y_max:
                    investments[company] = 'Инвестиции в кампанию нежелательны'
                else:
                    investments[
                        company] = 'Кампания развивается положительно, инвестиции могут окупиться в несколько раз'
                plt.plot(x_data, y_data, label=company)
            plt.title('Общий график отдачи операционных расходов (по рассмотренным компаниям)', fontsize=6)
            plt.xlabel('Операционные затраты, млрд. руб.', fontsize=6)
            plt.ylabel('Операционные доходы, млрд. руб.', fontsize=6)
            plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=6)
            plt.grid()
            plt.savefig('app/static/app/graph.png', bbox_inches='tight')
            show_graph = True
    else:
        form = BCoeffForm()
    return render(request, 'app/statistics.html', {'investments': investments, 'form': form, 'show_graph': show_graph})
