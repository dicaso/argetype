"""apetype reports module

Defines a TaskReport class, that using the leopard Report class
automatically builds a report as the Task is running.

Task subtasks can inject 'print' which then ensures that any
print statements are included in the report

Example:
    >>> from apetype.reports import TaskReport, TaskSection
    ... class Report(TaskReport):
    ...     title = 'An experimental report'
    ...     outfile = '/tmp/exreport'
    ...
    ...     def section_1(_) -> TaskSection:
    ...         import pandas as pd
    ...         return [
    ...           ('tab1', pd.DataFrame({'a': [1, 2], 'b': ['c', 'd']})),
    ...           ('tab2', pd.DataFrame({'c': [1, 2], 'd': ['c', 'd']}))
    ...         ]
    ...
    ...     def section_2_with_figure(_) -> TaskSection:
    ...         import matplotlib.pyplot as plt
    ...         print('Where will this end up?')
    ...         fig, ax = plt.subplots()
    ...         ax.scatter(range(5),range(5))
    ...         return {
    ...           'figures':{'fig 1':fig},
    ...           'clearpage':True
    ...         }

"""

from .tasks import TaskBase, PrintInject, ReturnTypeInterface

class TaskReport(TaskBase, PrintInject):
    def run(self, *args, show=True, **kwargs):
        # leopard needs to have been installed
        # if not `pip install leopard`
        # args and kwargs passed to super run
        import leopard as lp
        self.report = lp.Report(
            title = self.title,
            outfile = self.outfile
        )
        super().run(*args, **kwargs)
        self.report.outputPDF(show=show)


class TaskSection(dict, ReturnTypeInterface):
    def __init__(self):
        ReturnTypeInterface.__init__(self, dict)

    def __call__(self, task, function, result):
        import inspect
        from collections import OrderedDict
        from matplotlib.figure import Figure
        import pandas as pd
        if isinstance(result, list):
            # Optionally result can be a list of tuples
            # figures and tables will then be extracted in order
            figures = OrderedDict([r for r in result if isinstance(r[1],Figure)])
            tables = OrderedDict(
                [r for r in result
                 if isinstance(r[1],pd.DataFrame)
                 or isinstance(r[1],pd.Series)]
            )
            result = dict([r for r in result if r[0] not in figures.keys() or tables.keys()])
            if figures: result['figures'] = figures
            if tables: result['tables'] = tables
        if 'title' not in result:
            result['title'] = function.replace('_', ' ').capitalize()
        if 'text' not in result and inspect.getdoc(task.__getattribute__(function)):
            result['text'] = inspect.getdoc(task.__getattribute__(function))
        if hasattr(task, '_printout'):
            if 'code' in result:
                result['code'] += task.print()
            else: result['code'] = task.print()
        section = self.postprocess(result)
        task.report.subs.append(section)
        return section
        
    def preprocess(self):
        pass

    def postprocess(self, result):
        import leopard as lp
        return lp.Section(**result)
