import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="儲能專案主管決策系統", layout="wide")
st.title("⚡ 企業電費試算與儲能財務決策工具 V18")
st.write("已校準：完美融合『自訂台電費率』與『三項電費差額（基本/流動/超約）』精準結算引擎")

# ----------------- 側邊欄：參數設定 -----------------
st.sidebar.header("⚙️ 1. 契約容量設定 (kW)")
with st.sidebar.expander("現況契約 (三段式/無儲能)", expanded=False):
    c_reg_curr = st.number_input("現況 - 經常契約", value=650, step=10)
    c_non_sum_curr = st.number_input("現況 - 非夏月", value=0, step=10)
    c_half_curr = st.number_input("現況 - 半尖峰", value=0, step=10)
    c_sat_curr = st.number_input("現況 - 週六半尖峰", value=0, step=10)
    c_off_curr = st.number_input("現況 - 離峰", value=0, step=10)

with st.sidebar.expander("未來契約 (批次生產/含儲能)", expanded=False):
    c_reg_fut = st.number_input("未來 - 經常契約", value=300, step=10)
    c_non_sum_fut = st.number_input("未來 - 非夏月", value=0, step=10)
    c_half_fut = st.number_input("未來 - 半尖峰", value=0, step=10)
    c_sat_fut = st.number_input("未來 - 週六半尖峰", value=350, step=10)
    c_off_fut = st.number_input("未來 - 離峰", value=0, step=10)

st.sidebar.header("💰 2. 台電費率設定 (元/度)")
with st.sidebar.expander("三段式 - 流動電費單價", expanded=False):
    r3_s_p = st.number_input("夏月 - 尖峰", value=9.39, format="%.2f")
    r3_s_h = st.number_input("夏月 - 半尖峰", value=5.85, format="%.2f")
    r3_s_sat = st.number_input("夏月 - 週六半尖峰", value=2.60, format="%.2f")
    r3_s_off = st.number_input("夏月 - 離峰", value=2.53, format="%.2f")
    r3_n_p = st.number_input("非夏月 - 尖峰", value=5.47, format="%.2f")
    r3_n_sat = st.number_input("非夏月 - 週六半尖峰", value=2.41, format="%.2f")
    r3_n_off = st.number_input("非夏月 - 離峰", value=2.32, format="%.2f")

with st.sidebar.expander("批次生產 - 流動電費單價", expanded=False):
    rb_s_p = st.number_input("批次夏月 - 尖峰", value=12.47, format="%.2f")
    rb_s_sat = st.number_input("批次夏月 - 週六半尖峰", value=3.26, format="%.2f")
    rb_s_off = st.number_input("批次夏月 - 離峰", value=3.18, format="%.2f")
    rb_n_p = st.number_input("批次非夏月 - 尖峰", value=11.79, format="%.2f")
    rb_n_sat = st.number_input("批次非夏月 - 週六半尖峰", value=3.00, format="%.2f")
    rb_n_off = st.number_input("批次非夏月 - 離峰", value=2.88, format="%.2f")

with st.sidebar.expander("基本費單價 (元/瓩)", expanded=False):
    b_s_reg = st.number_input("夏月 - 經常單價", value=223.6, format="%.1f")
    b_n_reg = st.number_input("非夏月 - 經常單價", value=166.9, format="%.1f")
    b_s_off = st.number_input("夏月 - 離峰單價", value=44.7, format="%.1f")
    b_n_off = st.number_input("非夏月 - 離峰單價", value=33.3, format="%.1f")

st.sidebar.header("🔋 3. 儲能櫃與財務參數")
ess_enabled = st.sidebar.checkbox("開啟儲能櫃模擬", value=True)
ess_cap = st.sidebar.number_input("容量 (kWh)", value=2349, step=100)
ess_pow = st.sidebar.number_input("最大功率 (kW)", value=1125, step=50)
ess_eff = st.sidebar.slider("充放電效率 (%)", 70, 100, 92) / 100.0

if ess_enabled:
    st.sidebar.markdown("---")
    ess_strategy = st.sidebar.selectbox("放電模式", ["全力輸出", "削峰填谷", "定額放電"], index=2)
    if ess_strategy == "削峰填谷":
        ess_target_kw = st.sidebar.number_input("削峰啟動門檻 (kW)", value=c_reg_fut)
    elif ess_strategy == "定額放電":
        ess_fixed_pow = st.sidebar.number_input("定額放電功率 (kW)", value=316, step=10)
    
    ess_allow_export = st.sidebar.checkbox("允許超額放電折抵 (對齊Excel)", value=True)
    ess_charge_margin = st.sidebar.number_input("充電安全餘裕 (kW)", value=0, step=5)
    
    st.sidebar.markdown("---")
    total_capex = st.sidebar.number_input("建置總成本 CAPEX (元)", value=18000000, step=500000)
    project_years = st.sidebar.number_input("評估年限 (年)", value=15, step=1, max_value=25, min_value=3)
    annual_opex = st.sidebar.number_input("每年維護費 OPEX (元/年)", value=271800, step=10000)
    deg_rate = st.sidebar.number_input("電池每年衰退率 (%)", value=3.0, step=0.1) / 100.0
else:
    ess_strategy = "未開啟"
    total_capex = 0

# ----------------- 數據處理模組 -----------------
uploaded_file = st.file_uploader("請上傳 15 分鐘用電明細 (CSV)", type="csv")

if uploaded_file is not None:
    try:
        file_bytes = uploaded_file.getvalue()
        success, df = False, None
        for encoding in ['utf-8-sig', 'big5', 'cp950', 'utf-8']:
            try:
                uploaded_file.seek(0)
                content = file_bytes.decode(encoding)
                lines = content.splitlines()
                header_idx = next(i for i, line in enumerate(lines[:15]) if '年月日' in line)
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, skiprows=header_idx, encoding=encoding)
                df.columns = df.columns.str.strip()
                if '年月日' in df.columns: 
                    success = True
                    break
            except Exception:
                continue

        if success:
            with st.spinner('正在精準計算時間與費率...'):
                df['西元日期'] = df['年月日'].apply(lambda x: str(int(str(x).split('/')[0])+1911)+'/'+'/'.join(str(x).split('/')[1:]) if '/' in str(x) and len(str(x).split('/')[0])==3 else str(x))
                df['標準時間'] = df['時分'].str.strip().replace('24:00', '00:00')
                df['完整時間'] = pd.to_datetime(df['西元日期'] + ' ' + df['標準時間'])
                df.loc[df['時分'].str.strip() == '24:00', '完整時間'] += pd.Timedelta(days=1)
                
                power_cols = ['尖峰', '半尖峰', '週六半尖峰', '離峰']
                for col in power_cols: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df['原始功率(kW)'] = df[power_cols].sum(axis=1)

                def process_row(row):
                    dt = row['完整時間'] - pd.Timedelta(minutes=1)
                    m, d, wd, h = dt.month, dt.day, dt.weekday(), dt.hour + dt.minute/60.0
                    is_sum = (m > 5 and m < 10) or (m == 5 and d >= 16) or (m == 10 and d <= 15)
                    
                    p_3s, r_3s = "3S_離峰", r3_s_off if is_sum else r3_n_off
                    if is_sum:
                        if wd < 5:
                            if 16 <= h < 22: p_3s, r_3s = "3S_夏月尖峰", r3_s_p
                            elif (9 <= h < 16) or (22 <= h < 24): p_3s, r_3s = "3S_半尖峰", r3_s_h
                        elif wd == 5 and 9 <= h < 24: p_3s, r_3s = "3S_週六半尖峰", r3_s_sat
                    else:
                        if wd < 5:
                            if (6 <= h < 11) or (14 <= h < 24): p_3s, r_3s = "3S_非夏月尖峰", r3_n_p
                        elif wd == 5 and ((6 <= h < 11) or (14 <= h < 24)): p_3s, r_3s = "3S_週六半尖峰", r3_n_sat

                    p_b, r_b = "B_離峰", rb_s_off if is_sum else rb_n_off
                    if 15.5 <= h < 21.5:
                        if wd < 5: 
                            p_b = "B_夏月尖峰" if is_sum else "B_非夏月尖峰"
                            r_b = rb_s_p if is_sum else rb_n_p
                        elif wd == 5: 
                            p_b = "B_週六半尖峰"
                            r_b = rb_s_sat if is_sum else rb_n_sat
                            
                    return pd.Series([p_3s, r_3s, p_b, r_b])

                df[['三段時段', '三段費率', '批次時段', '批次費率']] = df.apply(process_row, axis=1)

            # --- 儲能充放電模擬 ---
            df['ESS功率(kW)'] = 0.0
            if ess_enabled:
                with st.spinner(f'正在模擬儲能櫃 [{ess_strategy}] 充放電...'):
                    curr_soc = 0.0
                    for i, row in df.iterrows():
                        actual_load = row['原始功率(kW)']
                        if row['批次時段'] == 'B_離峰' and curr_soc < ess_cap:
                            max_allowable = c_reg_fut + c_non_sum_fut + c_half_fut + c_sat_fut + c_off_fut
                            safe_margin = max(0, max_allowable - actual_load - ess_charge_margin)
                            charge = min(ess_pow, (ess_cap - curr_soc) / 0.25, safe_margin)
                            df.at[i, 'ESS功率(kW)'] = -charge
                            curr_soc += charge * 0.25 * ess_eff
                        
                        elif row['批次時段'] in ['B_夏月尖峰', 'B_非夏月尖峰'] and curr_soc > 0:
                            discharge = 0
                            if ess_strategy == "全力輸出":
                                discharge = min(ess_pow, curr_soc / 0.25) if ess_allow_export else min(ess_pow, curr_soc / 0.25, actual_load)
                            elif ess_strategy == "削峰填谷":
                                if actual_load > ess_target_kw:
                                    discharge = min(ess_pow, curr_soc / 0.25, actual_load - ess_target_kw)
                            elif ess_strategy == "定額放電":
                                discharge = min(ess_pow, curr_soc / 0.25, ess_fixed_pow) if ess_allow_export else min(ess_pow, curr_soc / 0.25, min(ess_fixed_pow, actual_load))

                            df.at[i, 'ESS功率(kW)'] = discharge
                            curr_soc -= discharge * 0.25

            df['原始度數(kWh)'] = df['原始功率(kW)'] * 0.25
            df['原始_三段流動'] = df['原始度數(kWh)'] * df['三段費率']
            df['原始_批次流動'] = df['原始度數(kWh)'] * df['批次費率']
            
            df['調整後功率(kW)'] = df['原始功率(kW)'] - df['ESS功率(kW)']
            df['調整後度數(kWh)'] = df['調整後功率(kW)'] * 0.25
            df['調整後_批次流動'] = df['調整後度數(kWh)'] * df['批次費率']

            # --- 月度彙整與電費計算 (恢復 V15 超約計算邏輯) ---
            df['年月'] = df['完整時間'].dt.strftime('%Y/%m')
            
            m_3s_orig = df.pivot_table(index='年月', columns='三段時段', values='原始功率(kW)', aggfunc='max').fillna(0)
            m_b_orig = df.pivot_table(index='年月', columns='批次時段', values='原始功率(kW)', aggfunc='max').fillna(0)
            m_b_adj = df.pivot_table(index='年月', columns='批次時段', values='調整後功率(kW)', aggfunc='max').fillna(0)
            m_flow = df.groupby('年月')[['原始_三段流動', '原始_批次流動', '調整後_批次流動']].sum()
            summary = pd.concat([m_flow], axis=1).reset_index()

            def calc_bills(row):
                m = int(row['年月'].split('/')[1])
                # 計算單月混合基本費率
                r_reg = b_s_reg if m in [6,7,8,9] else (b_n_reg*15 + b_s_reg*16)/31 if m==5 else (b_s_reg*15 + b_n_reg*16)/31 if m==10 else b_n_reg
                r_off = b_s_off if m in [6,7,8,9] else (b_n_off*15 + b_s_off*16)/31 if m==5 else (b_s_off*15 + b_n_off*16)/31 if m==10 else b_n_off
                
                non_sum_ratio = 1 if m in [11,12,1,2,3,4] else 15/31 if m==5 else 16/31 if m==10 else 0
                
                base_fee_curr = (c_reg_curr * r_reg) + (c_non_sum_curr * r_reg * non_sum_ratio) + (c_half_curr * r_reg) + ((c_sat_curr + c_off_curr) * r_off)
                base_fee_fut = (c_reg_fut * r_reg) + (c_non_sum_fut * r_reg * non_sum_ratio) + (c_half_fut * r_reg) + ((c_sat_fut + c_off_fut) * r_off)

                def get_over(m_data, t_cols, thresholds):
                    return max([max(0, m_data.loc[row['年月']].get(col, 0) - th) for col, th in zip(t_cols, thresholds)])
                
                th_3s_curr = [c_reg_curr, c_reg_curr+c_non_sum_curr, c_reg_curr+c_non_sum_curr+c_half_curr, c_reg_curr+c_non_sum_curr+c_half_curr+c_sat_curr, c_reg_curr+c_non_sum_curr+c_half_curr+c_sat_curr+c_off_curr]
                col_3s = ['3S_夏月尖峰', '3S_非夏月尖峰', '3S_半尖峰', '3S_週六半尖峰', '3S_離峰']
                
                th_b_fut = [c_reg_fut, c_reg_fut+c_non_sum_fut, c_reg_fut+c_non_sum_fut+c_sat_fut, c_reg_fut+c_non_sum_fut+c_sat_fut+c_off_fut]
                col_b = ['B_夏月尖峰', 'B_非夏月尖峰', 'B_週六半尖峰', 'B_離峰']

                o_3s_orig = get_over(m_3s_orig, col_3s, th_3s_curr)
                o_b_orig = get_over(m_b_orig, col_b, th_b_fut)
                o_b_adj = get_over(m_b_adj, col_b, th_b_fut)

                def get_pen(kw, limit_base):
                    limit = limit_base * 0.1
                    return 0 if kw <= 0 else ((kw * r_reg * 2) if kw <= limit else (limit * r_reg * 2) + ((kw - limit) * r_reg * 3))

                pen_curr = get_pen(o_3s_orig, c_reg_curr)
                
                if ess_enabled:
                    pen_fut = get_pen(o_b_adj, c_reg_fut)
                    flow_fut = row['調整後_批次流動']
                else:
                    pen_fut = get_pen(o_b_orig, c_reg_fut)
                    flow_fut = row['原始_批次流動']

                flow_curr = row['原始_三段流動']

                diff_base = base_fee_curr - base_fee_fut
                diff_flow = flow_curr - flow_fut
                diff_pen = pen_curr - pen_fut
                monthly_save = diff_base + diff_flow + diff_pen

                return pd.Series([diff_base, diff_flow, diff_pen, monthly_save, (base_fee_curr+pen_curr+flow_curr), (base_fee_fut+pen_fut+flow_fut)])

            summary[['基本電費差', '流動電費差', '超約費差', '每月可節省', '現況總費', '方案總費']] = summary.apply(calc_bills, axis=1)
            st.success(f"✅ 計算完成！")

            # ==========================================
            # 管理階層儀表板區塊
            # ==========================================
            yr1_save = summary['每月可節省'].sum()
            total_current = summary['現況總費'].sum()
            total_future = summary['方案總費'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("現況年度總電費 (三段式)", f"${total_current:,.0f}")
            c2.metric("方案年度總電費 (批次+儲能)", f"${total_future:,.0f}")
            c3.metric("🎉 第一年總節省金額", f"${yr1_save:,.0f}", delta=f"${yr1_save:,.0f} / 年")
            
            st.divider()

            col_left, col_right = st.columns([1, 1.2])

            with col_left:
                st.subheader("📋 1~12 月份節省金額明細")
                display_cols = ['年月', '基本電費差', '流動電費差', '超約費差', '每月可節省']
                format_dict_summary = {c: "{:,.0f}" for c in display_cols if c != '年月'}
                st.dataframe(summary[display_cols].style.format(format_dict_summary))

            with col_right:
                st.subheader(f"💰 0 ~ {project_years} 年專案現金流與回收狀況")
                
                cf_project = [-total_capex]
                for yr in range(1, int(project_years) + 1):
                    efficiency_factor = (1 - deg_rate) ** (yr - 1)
                    net_cash = (yr1_save * efficiency_factor) - annual_opex
                    cf_project.append(net_cash)

                cum_cf = np.cumsum(cf_project)
                real_payback = -1
                for i in range(1, len(cum_cf)):
                    if cum_cf[i] >= 0:
                        fraction = abs(cum_cf[i-1]) / cf_project[i]
                        real_payback = (i - 1) + fraction
                        break

                def calc_irr(cash_flows):
                    if sum(cash_flows) < 0: return -1.0
                    rate = 0.05
                    for _ in range(100):
                        npv = sum([c / (1 + rate)**i for i, c in enumerate(cash_flows)])
                        derivative = sum([-i * c / (1 + rate)**(i + 1) for i, c in enumerate(cash_flows)])
                        if abs(derivative) < 1e-6: break
                        rate -= npv / derivative
                        if abs(npv) < 1e-4: return rate
                    return rate

                irr_val = calc_irr(cf_project)
                
                m1, m2 = st.columns(2)
                m1.metric("預估 IRR (內部報酬率)", f"{irr_val * 100:.2f}%" if irr_val >= 0 else "無法回本")
                m2.metric("真實動態回收期", f"約 {real_payback:.1f} 年" if real_payback > 0 else "年限內無法回本")
                
                cf_df = pd.DataFrame({
                    "年份": [f"第 {i} 年" if i > 0 else "第 0 年 (投入成本)" for i in range(len(cf_project))],
                    "每年節省淨額 (扣除OPEX與衰退)": cf_project,
                    "累計現金狀態": cum_cf
                }).set_index("年份")
                
                def color_negative_red(val):
                    color = 'red' if val < 0 else 'green'
                    return f'color: {color}'
                
                st.dataframe(cf_df.style.map(color_negative_red).format("{:,.0f}"))

            # ----------------- CSV 匯出下載功能 -----------------
            st.markdown("---")
            st.subheader("📥 下載分析報表")
            
            col_dl1, col_dl2 = st.columns(2)
            csv_summary = summary[display_cols].to_csv(index=False).encode('utf-8-sig')
            col_dl1.download_button("📊 下載【每月節省金額明細】CSV", data=csv_summary, file_name="儲能專案月度節省差額.csv", mime="text/csv")
            
            if ess_enabled:
                csv_cf = cf_df.to_csv().encode('utf-8-sig')
                col_dl2.download_button("💰 下載【0~N年完整現金流】CSV", data=csv_cf, file_name="儲能專案長期現金流.csv", mime="text/csv")

    except Exception as e:
        # 【關鍵修正】這行會印出真正的 Python 錯誤，幫助我們抓蟲
        st.error(f"分析失敗，錯誤詳細資訊：{str(e)}")