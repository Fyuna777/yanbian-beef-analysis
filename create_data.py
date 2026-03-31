import pandas as pd
import os

# 定义数据
data = {
    '渠道': ['小红书', '抖音', '拼多多', '线下活动'],
    'ROI': [3.8, 2.5, 1.9, 2.2],
    '转化率': [0.023, 0.018, 0.012, 0.015],
    'CAC': [45, 68, 52, 75]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 确保data文件夹存在
os.makedirs('data', exist_ok=True)

# 保存为CSV文件
file_path = 'data/channel_performance.csv'
df.to_csv(file_path, index=False, encoding='utf-8-sig')

print(f'CSV文件已成功创建在: {file_path}')
print('文件内容预览:')
print(df)