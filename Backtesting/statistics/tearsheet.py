from .base import AbstractStatistics
import Backtesting.statistics.performance as perf


from matplotlib.ticker import FuncFormatter
from matplotlib import cm


import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.dates as mdates
import seaborn as sns
import os
import datetime


class TearsheetStatistics(AbstractStatistics):
    """
    Displays a Matplotlib-generated 'one-pager' as often
    found in institutional strategy performance reports.

    Includes an equity curve, drawdown curve, monthly
    returns heatmap, yearly returns summary, strategy-
    level statistics and trade-level statistics.

    Also includes an optional annualised rolling Sharpe
    ratio chart.
    """
    def __init__(
        self, output_dir, portfolio_handler,
        title=None, benchmark=None, periods=252,
        rolling_sharpe=False
    ):
        """
        Takes in a portfolio handler.
        """
        self.portfolio_handler = portfolio_handler
        self.output_dir = output_dir
        self.data_handler = portfolio_handler.data_handler
        self.title = '\n'.join(title)
        self.benchmark = benchmark
        self.periods = periods
        self.equity = {}
        self.equity_benchmark = {}
        self.log_scale = False
        self.statistics = {}

    def update(self, timestamp, portfolio_handler):
        """
        Update equity curve and benchmark equity curve that must be tracked
        over time.
        """
        self.equity[timestamp] = self.portfolio_handler.portfolio.equity

        if self.benchmark is not None:
            self.equity_benchmark[timestamp] = self.data_handler.get_last_close(self.benchmark)

    def get_results(self):
        """
        Return a dict with all important results & stats.
        """
        # Equity
        equity_s = pd.Series(self.equity).sort_index()

        # Returns
        returns_s = equity_s.pct_change().fillna(0.0)

        # Rolling Annualised Sharpe
        rolling = returns_s.rolling(window=self.periods)
        rolling_sharpe_s = np.sqrt(self.periods) * (
            rolling.mean() / rolling.std()
        )

        # Cummulative Returns
        cum_returns_s = np.exp(np.log(1 + returns_s).cumsum())

        # Drawdown, max drawdown, max drawdown duration
        dd_s, max_dd, max_dd_start, max_dd_end, max_dd_dur = perf.create_drawdowns(cum_returns_s)       

        # Equity statistics
        self.statistics["sharpe"] = perf.create_sharpe_ratio(
            returns_s, self.periods
        )
        self.statistics["drawdowns"] = dd_s
        self.statistics["max_drawdown"] = max_dd
        self.statistics["max_drawdown_pct"] = max_dd
        self.statistics["max_drawdown_start"] = max_dd_start
        self.statistics["max_drawdown_end"] = max_dd_end
        self.statistics["max_drawdown_duration"] = max_dd_dur
        self.statistics["equity"] = equity_s
        self.statistics["returns"] = returns_s
        self.statistics["rolling_sharpe"] = rolling_sharpe_s
        self.statistics["cum_returns"] = cum_returns_s
        self.statistics["total_return"] = cum_returns_s[-1] - 1

        positions = self._get_positions()
        if positions is not None:
            self.statistics["positions"] = positions

        # Benchmark self.statistics if benchmark ticker specified
        if self.benchmark is not None:
            equity_b = pd.Series(self.equity_benchmark).sort_index()
            returns_b = equity_b.pct_change().fillna(0.0)
            rolling_b = returns_b.rolling(window=self.periods)
            rolling_sharpe_b = np.sqrt(self.periods) * (
                rolling_b.mean() / rolling_b.std()
            )
            cum_returns_b = np.exp(np.log(1 + returns_b).cumsum())
            dd_b, max_dd_b, max_dd_start_b, max_dd_end_b, max_dd_dur_b = perf.create_drawdowns(cum_returns_b)
            self.statistics["sharpe_b"] = perf.create_sharpe_ratio(returns_b)
            self.statistics["drawdowns_b"] = dd_b
            self.statistics["max_drawdown_b"] = max_dd_b
            self.statistics["max_drawdown_start_b"] = max_dd_start_b
            self.statistics["max_drawdown_end_b"] = max_dd_end_b
            self.statistics["max_drawdown_duration_b"] = max_dd_dur_b
            self.statistics["equity_b"] = equity_b
            self.statistics["returns_b"] = returns_b
            self.statistics["rolling_sharpe_b"] = rolling_sharpe_b
            self.statistics["cum_returns_b"] = cum_returns_b

        return self.statistics
        
    def _get_positions(self):
        """
        Retrieve the list of closed Positions objects from the portfolio
        and reformat into a pandas dataframe to be returned
        """
        pos = self.portfolio_handler.portfolio.closed_positions
        a = []
        for p in pos:
            a.append(p.__dict__)
        if len(a) == 0:
            # There are no closed positions
            return None
        else:
            df = pd.DataFrame(a)
            # df['trade_pct'] = (df['avg_sld'] / df['avg_bot'] - 1.0)
            pass
            return df

    def _plot_equity(self, stats, ax=None, **kwargs):
        """
        Plots cumulative rolling returns versus some benchmark.
        """
        equity = stats['cum_returns']
        if ax is None:
            ax = plt.gca()
            
        def format_two_dec(x, pos):
            return '%.2f' % x
        y_axis_formatter = FuncFormatter(format_two_dec)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')
        
        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.set_minor_locator(mdates.MonthLocator())
        ax.xaxis.grid(linewidth=1, linestyle=':', which = 'major')
        ax.xaxis.grid(linewidth=0.5, linestyle=':', which = 'minor')

        if self.benchmark is not None:
            benchmark = self.statistics['cum_returns_b']
            benchmark.plot(
                lw=2, color='gray', label=self.benchmark, alpha=0.60,
                ax=ax, **kwargs
            )

        equity.plot(
            lw=2, color='green', label='Backtest', alpha=0.6,
            ax=ax, **kwargs
        )

        ax.axhline(1.0, linestyle='--', color='black', lw=1)
        ax.set_ylabel('Cumulative returns')
        ax.legend(loc='best')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        plt.grid(True)
        if self.log_scale:
            ax.set_yscale('log')

        return ax


    def _plot_drawdown(self, stats, ax=None, **kwargs):
        """
        Plots the underwater curve
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        drawdown = stats['drawdowns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')
        ax.xaxis.set_tick_params(reset=True)
        ax.xaxis.set_major_locator(mdates.YearLocator(1))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
        ax.xaxis.grid(linestyle=':')

        underwater = -100 * drawdown
        underwater.plot(ax=ax, lw=2, kind='area', color='red', alpha=0.3, **kwargs)
        ax.set_ylabel('')
        ax.set_xlabel('')
        plt.setp(ax.get_xticklabels(), visible=True, rotation=0, ha='center')
        ax.set_title('Drawdown (%)', fontweight='bold')
        return ax

    def _plot_monthly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a heatmap of the monthly returns.
        """
        returns = stats['returns']
        if ax is None:
            ax = plt.gca()

        monthly_ret = perf.aggregate_returns(returns, 'monthly')
        monthly_ret = monthly_ret.unstack()
        monthly_ret = np.round(monthly_ret, 3)
        monthly_ret.rename(
            columns={1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr',
                     5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Aug',
                     9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'},
            inplace=True
        )

        sns.heatmap(
            monthly_ret.fillna(0) * 100.0,
            annot=True,
            fmt="0.1f",
            annot_kws={"size": 8},
            alpha=1.0,
            center=0.0,
            cbar=False,
            cmap=cm.RdYlGn,
            ax=ax, **kwargs)
        ax.set_title('Monthly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
        ax.set_xlabel('')

        return ax

    def _plot_yearly_returns(self, stats, ax=None, **kwargs):
        """
        Plots a barplot of returns by year.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats['returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))
        ax.yaxis.grid(linestyle=':')

        yly_ret = perf.aggregate_returns(returns, 'yearly') * 100.0
        yly_ret.plot(ax=ax, kind="bar")
        ax.set_title('Yearly Returns (%)', fontweight='bold')
        ax.set_ylabel('')
        ax.set_xlabel('')
        ax.set_xticklabels(ax.get_xticklabels(), rotation=15, ha='center')
        ax.xaxis.grid(False)

        return ax

    def _plot_txt_curve(self, stats, ax=None, **kwargs):
        """
        Outputs the statistics for the equity curve.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats["returns"]
        cum_returns = stats['cum_returns']
        tot_ret = stats["total_return"]
        sharpe = self.statistics["sharpe"]
        
        
        max_dd = self.statistics["max_drawdown"]
        max_dd_start = self.statistics["max_drawdown_start"]
        max_dd_end = self.statistics["max_drawdown_end"]
        max_dd_dur = self.statistics["max_drawdown_duration"]


        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        cagr = perf.create_cagr(cum_returns, self.periods)
        sortino = perf.create_sortino_ratio(returns, self.periods)

        ax.text(0.25, 8.7, 'Total Return', fontsize=9)
        ax.text(7.50, 8.7, '{:.0%}'.format(tot_ret), fontweight='bold', horizontalalignment='right', fontsize=9)

        ax.text(0.25, 7.7, 'CAGR', fontsize=9)
        ax.text(7.50, 7.7, '{:.2%}'.format(cagr), fontweight='bold', horizontalalignment='right', fontsize=9)

        ax.text(0.25, 6.7, 'Sharpe Ratio', fontsize=9)
        ax.text(7.50, 6.7, '{:.2f}'.format(sharpe), color='red', fontweight='bold', horizontalalignment='right', 
        fontsize=9)

        ax.text(0.25, 5.7, 'Sortino Ratio', fontsize=9)
        ax.text(7.50, 5.7, '{:.2f}'.format(sortino), fontweight='bold', horizontalalignment='right', fontsize=9)

        ax.text(0.25, 4.7, 'Annual Volatility', fontsize=9)
        ax.text(7.50, 4.7, '{:.2%}'.format(returns.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=9)
        
        ax.text(0.25, 3.7, 'Max Drawdown Duration', fontsize=9)
        ax.text(7.50, 3.7, '{:.0f}'.format(max_dd_dur), fontweight='bold', horizontalalignment='right', fontsize=9)

        ax.text(0.25, 2.7, 'Max Drawdown', fontsize=9)
        ax.text(7.50, 2.7, '{:.2%}'.format(max_dd), color='red', fontweight='bold', horizontalalignment='right', fontsize=9)
        
        ax.text(0.25, 1.7, 'Max Drawdown Start', fontsize=9)
        ax.text(7.50, 1.7, '{}'.format(max_dd_start), fontweight='bold', horizontalalignment='right', fontsize=9)
        
        ax.text(0.25, 0.7, 'Max Drawdown End', fontsize=9)
        ax.text(7.50, 0.7, '{}'.format(max_dd_end), fontweight='bold', horizontalalignment='right', fontsize=9)


        ax.set_title('Curve', fontweight='bold')

        if self.benchmark is not None:
            returns_b = stats['returns_b']
            equity_b = stats['cum_returns_b']
            tot_ret_b = equity_b[-1] - 1.0
            cagr_b = perf.create_cagr(equity_b)
            sharpe_b = self.statistics["sharpe_b"]
            sortino_b = perf.create_sortino_ratio(returns_b)            
            max_dd_b = self.statistics["max_drawdown_b"]
            max_dd_dur_b = self.statistics["max_drawdown_duration_b"]

            ax.text(9.75, 8.7, '{:.0%}'.format(tot_ret_b), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 7.7, '{:.2%}'.format(cagr_b), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 6.7, '{:.2f}'.format(sharpe_b), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 5.7, '{:.2f}'.format(sortino_b), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 4.7, '{:.2%}'.format(returns_b.std() * np.sqrt(252)), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 3.7, '{:.0f}'.format(max_dd_dur_b), fontweight='bold', horizontalalignment='right', fontsize=9)
            ax.text(9.75, 2.7, '{:.2%}'.format(max_dd_b), color='red', fontweight='bold', horizontalalignment='right', fontsize=9)

            ax.set_title('Curve vs. Benchmark', fontweight='bold')

        ax.grid(False)
        ax.spines['top'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax.axis([0, 10, 0, 10])
        return ax


    def _plot_txt_time(self, stats, ax=None, **kwargs):
        """
        Outputs the statistics for various time frames.
        """
        def format_perc(x, pos):
            return '%.0f%%' % x

        returns = stats['returns']

        if ax is None:
            ax = plt.gca()

        y_axis_formatter = FuncFormatter(format_perc)
        ax.yaxis.set_major_formatter(FuncFormatter(y_axis_formatter))

        mly_ret = perf.aggregate_returns(returns, 'monthly')
        yly_ret = perf.aggregate_returns(returns, 'yearly')

        mly_pct = mly_ret[mly_ret >= 0].shape[0] / float(mly_ret.shape[0])
        mly_avg_win_pct = np.mean(mly_ret[mly_ret >= 0])
        mly_avg_loss_pct = np.mean(mly_ret[mly_ret < 0])
        mly_max_win_pct = np.max(mly_ret)
        mly_max_loss_pct = np.min(mly_ret)
        yly_pct = yly_ret[yly_ret >= 0].shape[0] / float(yly_ret.shape[0])
        yly_max_win_pct = np.max(yly_ret)
        yly_max_loss_pct = np.min(yly_ret)

        ax.text(0.5, 8.7, 'Winning Months %', fontsize=9)
        ax.text(9.5, 8.7, '{:.0%}'.format(mly_pct), fontsize=9, fontweight='bold',
                horizontalalignment='right')

        ax.text(0.5, 7.7, 'Average Winning Month %', fontsize=9)
        ax.text(9.5, 7.7, '{:.2%}'.format(mly_avg_win_pct), fontsize=9, fontweight='bold',
                color='red' if mly_avg_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 6.7, 'Average Losing Month %', fontsize=9)
        ax.text(9.5, 6.7, '{:.2%}'.format(mly_avg_loss_pct), fontsize=9, fontweight='bold',
                color='red' if mly_avg_loss_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 5.7, 'Best Month %', fontsize=9)
        ax.text(9.5, 5.7, '{:.2%}'.format(mly_max_win_pct), fontsize=9, fontweight='bold',
                color='red' if mly_max_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 4.7, 'Worst Month %', fontsize=9)
        ax.text(9.5, 4.7, '{:.2%}'.format(mly_max_loss_pct), fontsize=9, fontweight='bold',
                color='red' if mly_max_loss_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 3.7, 'Winning Years %', fontsize=9)
        ax.text(9.5, 3.7, '{:.0%}'.format(yly_pct), fontsize=9, fontweight='bold',
                horizontalalignment='right')

        ax.text(0.5, 2.7, 'Best Year %', fontsize=9)
        ax.text(9.5, 2.7, '{:.2%}'.format(yly_max_win_pct), fontsize=9,
                fontweight='bold', color='red' if yly_max_win_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 1.7, 'Worst Year %', fontsize=9)
        ax.text(9.5, 1.7, '{:.2%}'.format(yly_max_loss_pct), fontsize=9,
                fontweight='bold', color='red' if yly_max_loss_pct < 0 else 'green',
                horizontalalignment='right')

        ax.text(0.5, 0.7, 'Final Equity', fontsize=9)
        ax.text(9.5, 0.7, '{:.2f}'.format(stats["equity"][-1]), fontsize=9, fontweight='bold', horizontalalignment='right')

        ax.set_title('Time', fontweight='bold')
        ax.grid(False)
        ax.spines['top'].set_linewidth(1.5)
        ax.spines['bottom'].set_linewidth(1.5)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.get_yaxis().set_visible(False)
        ax.get_xaxis().set_visible(False)
        ax.set_ylabel('')
        ax.set_xlabel('')

        ax.axis([0, 10, 0, 10])
        return ax

    def plot_results(self, filename=None):
        """
        Plot the Tearsheet
        """
        rc = {
            'lines.linewidth': 1.0,
            'axes.facecolor': '0.995',
            'figure.facecolor': '0.97',
            'font.family': 'serif',
            'font.serif': 'Ubuntu',
            'font.monospace': 'Ubuntu Mono',
            'font.size': 10,
            'axes.labelsize': 10,
            'axes.labelweight': 'bold',
            'axes.titlesize': 10,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 10,
            'figure.titlesize': 12
        }
        sns.set_context(rc)
        sns.set_style("whitegrid")
        sns.set_palette("deep", desat=.6)
        
        vertical_sections = 5
        fig = plt.figure(figsize=(14, vertical_sections * 3.5))
        fig.suptitle(self.title, y=0.98, weight='bold', fontsize=12)
        gs = gridspec.GridSpec(vertical_sections, 6, wspace=0.25, hspace=0.5)
        
        ax_equity = plt.subplot(gs[:2, :])
        ax_drawdown = plt.subplot(gs[2, :])
        ax_monthly_returns = plt.subplot(gs[3, :4])
        ax_yearly_returns = plt.subplot(gs[3, 4:6])
        ax_txt_curve = plt.subplot(gs[4, 0:3])
        ax_txt_time = plt.subplot(gs[4, 3:6])
        
        stats = self.statistics
        self._plot_equity(stats, ax=ax_equity)
        self._plot_drawdown(stats, ax=ax_drawdown)
        self._plot_monthly_returns(stats, ax=ax_monthly_returns)
        self._plot_yearly_returns(stats, ax=ax_yearly_returns)
        self._plot_txt_curve(stats, ax=ax_txt_curve)
        self._plot_txt_time(stats, ax=ax_txt_time)
        
        
        plt.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.05)
        # Plot the figure
        plt.show()

        if filename is not None:
            fig.savefig(filename, dpi=150, bbox_inches='tight')

    def get_filename(self, filename=""):
        if filename == "":
            now = datetime.datetime.utcnow()
            filename = "backtest_" + now.strftime("%Y-%m-%d_%H%M%S") + ".png"
            filename = os.path.expanduser(os.path.join(self.output_dir, filename))
        return filename

    def save(self, filename=""):
        filename = self.get_filename(filename)
        self.plot_results(filename)
