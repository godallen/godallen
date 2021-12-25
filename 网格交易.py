# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
import numpy as np
import pandas as pd
from gm.api import *

'''
本策略标的为：SHFE.rb1901
价格中枢设定为：前一交易日的收盘价
从阻力位到压力位分别为：1.03 * open、1.02 * open、1.01 * open、open、0.99 * open、0.98 * open、0.97 * open
每变动一个网格，交易量变化100个单位
回测数据为:SHFE.rb1901的1min数据
回测时间为:2017-07-01 08:00:00到2017-10-01 16:00:00
'''

def init(context):
    # 策略标的为SHFE.rb1901
    context.symbol = 'SHFE.rb2201'

    # 订阅SHFE.rb1901, bar频率为1min
    subscribe(symbols=context.symbol, frequency='60s')

    # 设置每变动一格，增减的数量
    context.volume = 1

    # 储存前一个网格所处区间，用来和最新网格所处区间作比较
    context.last_grid = 0

    # 以前一日的收盘价为中枢价格
    context.center = history_n(symbol=context.symbol, frequency='1d', end_time=context.now, count=1, fields='close')[0]['close']

    # 记录上一次交易时网格范围的变化情况（例如从4区到5区，记为4,5）
    context.grid_change_last = [0, 0]


def on_bar(context, bars):
    bar = bars[0]

    # 获取多仓仓位
    position_long = context.account().position(symbol=context.symbol, side=PositionSide_Long)

    # 获取空仓仓位
    position_short = context.account().position(symbol=context.symbol, side=PositionSide_Short)

    # 设置网格和当前价格所处的网格区域
    context.band = np.array([0.97, 0.98, 0.99, 1, 1.01, 1.02, 1.03]) * context.center
    grid = pd.cut([bar.close], context.band, labels=[1, 2, 3, 4, 5, 6])[0]

    # 如果价格超出网格设置范围，则提示调节网格宽度和数量
    if np.isnan(grid):
        print('价格波动超过网格范围，可适当调节网格宽度和数量')

    # 如果新的价格所处网格区间和前一个价格所处的网格区间不同，说明触碰到了网格线，需要进行交易
    # 如果新网格大于前一天的网格，做空或平多
    if context.last_grid < grid:
        # 记录新旧格子范围（按照大小排序）
        grid_change_new = [context.last_grid,grid]

        # 几种例外：
        # 当last_grid = 0 时是初始阶段，不构成信号
        # 如果此时grid = 3，说明当前价格仅在开盘价之下的3区域中，没有突破网格线
        # 如果此时grid = 4，说明当前价格仅在开盘价之上的4区域中，没有突破网格线
        if context.last_grid == 0:
            context.last_grid = grid
            return

        if context.last_grid != 0:
            # 如果前一次开仓是4-5，这一次是5-4，算是没有突破，不成交
            if grid_change_new != context.grid_change_last:
                # 更新前一次的数据
                context.last_grid = grid
                context.grid_change_last = grid_change_new

                # 如果有多仓，平多
                if position_long:
                    order_volume(symbol=context.symbol, volume=context.volume, side=OrderSide_Sell, order_type=OrderType_Market,
                                 position_effect=PositionEffect_Close)
                    print('以市价单平多仓{}手'.format(context.volume))

                # 否则，做空
                if not position_long:
                    order_volume(symbol=context.symbol, volume=context.volume, side=OrderSide_Sell, order_type=OrderType_Market,
                                 position_effect=PositionEffect_Open)
                    print('以市价单开空{}手'.format(context.volume))

    # 如果新网格小于前一天的网格，做多或平空
    if context.last_grid > grid:
        # 记录新旧格子范围（按照大小排序）
        grid_change_new = [grid, context.last_grid]

        # 几种例外：
        # 当last_grid = 0 时是初始阶段，不构成信号
        # 如果此时grid = 3，说明当前价格仅在开盘价之下的3区域中，没有突破网格线
        # 如果此时grid = 4，说明当前价格仅在开盘价之上的4区域中，没有突破网格线
        if context.last_grid == 0:
            context.last_grid = grid
            return

        if context.last_grid != 0:
            # 如果前一次开仓是4-5，这一次是5-4，算是没有突破，不成交
            if grid_change_new != context.grid_change_last:
                # 更新前一次的数据
                context.last_grid = grid
                context.grid_change_last = grid_change_new

                # 如果有空仓，平空
                if position_short:
                    order_volume(symbol=context.symbol, volume=context.volume, side=OrderSide_Buy,
                                 order_type=OrderType_Market,
                                 position_effect=PositionEffect_Close)
                    print('以市价单平空仓{}手'.format(context.volume))

                # 否则，做多
                if not position_short:
                    order_volume(symbol=context.symbol, volume=context.volume, side=OrderSide_Buy,
                                 order_type=OrderType_Market,
                                 position_effect=PositionEffect_Open)
                    print('以市价单开多{}手'.format(context.volume))


    # 设计一个止损条件：当持仓量达到10手，全部平仓
    if position_short == 10 or position_long == 10:
        order_close_all()
        print('触发止损，全部平仓')


if __name__ == '__main__':
    '''
    strategy_id策略ID,由系统生成
    filename文件名,请与本文件名保持一致
    mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
    token绑定计算机的ID,可在系统设置-密钥管理中生成
    backtest_start_time回测开始时间
    backtest_end_time回测结束时间
    backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
    backtest_initial_cash回测初始资金
    backtest_commission_ratio回测佣金比例
    backtest_slippage_ratio回测滑点比例
    '''
    run(strategy_id='a531bcd8-5be5-11ec-8d94-d68a3b13928c',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='bacc3f30ab3ef2ce0f3a5037fcbef01f2190b1c0',
        backtest_start_time='2021-07-01 08:00:00',
        backtest_end_time='2021-11-01 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=100000,
        backtest_commission_ratio=0.0001,
        backtest_slippage_ratio=0.0001)
