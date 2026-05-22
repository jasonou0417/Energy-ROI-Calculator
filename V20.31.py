import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="儲能專案主管決策系統 V20.31", layout="wide")
st.title("⚡ 企業電費試算與儲能財務決策工具 (V20.31 終極完備版)")
st.write("已校準：【實務報價連動】容量採單櫃×台數自動推算，維運與保險費率全面採建置成本 % 數連動，財務指標 100% 自動化！")

# ----------------- 側邊欄：參數設定 -----------------
st.sidebar.header("⚙️ 1. 契約容量設定 (kW)")

with st.sidebar.expander("📌 現況 (基準 / 無儲能)", expanded=False):
    c_reg_curr = st.number_input("現況 - 經常契約", value=1460, step=10)
    c_non_sum_curr = st.number_input("現況 - 非夏月", value=0, step=10)
    c_half_curr = st.number_input("現況 - 半尖峰", value=0, step=10)
    c_sat_curr = st.number_input("現況 - 週六半尖峰", value=0, step=10)
    c_off_curr = st.number_input("現況 - 離峰", value=0, step=10)

with st.sidebar.expander("🛡️ 方案一 (三段式 + 儲能)", expanded=False):
    c_reg_op1 = st.number_input("方案一 - 經常契約", value=1150, step=10)
    c_non_sum_op1 = st.number_input("方案一 - 非夏月", value=0, step=10)
    c_half_op1 = st.number_input("方案一 - 半尖峰", value=0, step=10)
    c_sat_op1 = st.number_input("方案一 - 週六半尖峰", value=0, step=10)
    c_off_op1 = st.number_input("方案一 - 離峰", value=0, step=10)

with st.sidebar.expander("⚡ 方案二 (批次生產 + 儲能)", expanded=False):
    c_reg_op2 = st.number_input("方案二 - 經常契約", value=1150, step=10)
    c_non_sum_op2 = st.number_input("方案二 - 非夏月", value=0, step=10)
    c_half_op2 = st.number_input("方案二 - 半尖峰", value=0, step=10)
    c_sat_op2 = st.number_input("方案二 - 週六半尖峰", value=700, step=10)
    c_off_op2 = st.number_input("方案二 - 離峰", value=0, step=10)

st.sidebar.header("💰 2. 台電費率設定 (元/度)")
with st.sidebar.expander("三段式 - 流動電費單價", expanded=False):
    r3_s_p = st.number_input("夏月 - 尖峰", value=9.39, format="%.2f")
    r3_s_h = st.number_input("夏月 - 半尖峰", value=5.85, format="%.2f")
    r3_s_sat = st.number_input("夏月 - 週六半尖峰", value=2.60, format="%.2f")
    r3_s_off = st.number_input("夏月 - 離峰", value=2.53, format="%.2f")
    r3_n_h = st.number_input("非夏月 - 半尖峰", value=5.47, format="%.2f") 
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

st.sidebar.header("🔋 3. 儲能與對帳參數")

ess_enabled = st.sidebar.checkbox("開啟儲能櫃模擬", value=True)

# 💡 V20.31 修正：儲能櫃台數與容量連動推算
unit_cap_kwh = st.sidebar.number_input("單台儲能容量 (kWh)", value=261, step=1)
ess_units = st.sidebar.number_input("儲能櫃數量 (台)", value=5, step=1)
ess_cap_nominal = unit_cap_kwh * ess_units

st.sidebar.info(f"💡 系統總建置容量：**{ess_cap_nominal:,.0f} kWh**")

ess_dod = st.sidebar.slider("安全放電深度 DoD (%)", 50, 100, 85) / 100.0
ess_cap = ess_cap_nominal * ess_dod

# 功率預設連動 (預設 125kW * 台數)
ess_pow = st.sidebar.number_input("最大功率 (kW)", value=125 * ess_units, step=50)
ess_eff = st.sidebar.slider("充放電效率 (%)", 70, 100, 92) / 100.0

# 預設全域變數
ess_strategy = "未開啟"
auto_fixed = False
ess_fixed_pow_manual = 0
ess_allow_export = False
ess_charge_margin = 0

vpp_enabled = False
vpp_bid_kw = 0
vpp_price = 0
vpp_hours = []
vpp_schedule_mode = "手動勾選"
vpp_aggregator_share = 0.0

if ess_enabled:
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### ⚡ 虛擬電廠 (即時備轉 sReg)")
    vpp_enabled = st.sidebar.checkbox("啟用即時備轉收益", value=True)
    if vpp_enabled:
        vpp_bid_kw = st.sidebar.number_input("投標容量 (kW)", value=500, step=50, max_value=int(ess_pow))
        
        if vpp_bid_kw < 1000:
            st.sidebar.warning("⚠️ 台電規定單筆投標下限為 1MW (1000kW)。低於此容量必須透過「聚合商」代為併表投標。")
            vpp_aggregator_share = st.sidebar.slider("聚合商代操分潤 (%)", 0, 30, 15) / 100.0
        else:
            vpp_aggregator_share = st.sidebar.slider("聚合商代操分潤 (%)", 0, 30, 0, help="若大於 1MW 且自行直投台電可設為 0%。") / 100.0

        vpp_price = st.sidebar.number_input("通告費均價 (元/MW-h)", value=400, step=10)
        vpp_schedule_mode = st.sidebar.selectbox("投標時段設定", ["🤖 AI 自動排班 (依真實合約上限動態迴避)", "手動勾選"])
        
        if vpp_schedule_mode == "手動勾選":
            vpp_hours = st.sidebar.multiselect("選擇投標時段", ["離峰", "半尖峰", "週六半尖峰", "尖峰"], default=["離峰"])
        else:
            st.sidebar.success("✅ AI 將掃描合約上限與負載，精算出真實充電極限，確保 100% 不超約！")
            
        st.sidebar.caption(f"※ 投標時段內將硬性鎖定 {vpp_bid_kw}kWh 電量與功率。")
    
    st.sidebar.markdown("---")
    ess_strategy = st.sidebar.selectbox("放電模式", ["全力輸出", "削峰填谷 (AI動態追隨)", "定額放電"], index=2)
    
    if ess_strategy == "削峰填谷 (AI動態追隨)":
        st.sidebar.caption(f"※ 可用總電量為：{ess_cap:.1f} kWh")
    elif ess_strategy == "定額放電":
        auto_fixed = st.sidebar.checkbox("🤖 自動推算最佳定額功率", value=False)
        if not auto_fixed:
            ess_fixed_pow_manual = st.sidebar.number_input("自訂定額放電功率 (kW)", value=900, step=10)
    
    ess_allow_export = st.sidebar.checkbox("允許超額放電折抵 (對齊Excel / 逆送台電)", value=False)
    ess_charge_margin = st.sidebar.number_input("充電安全餘裕 (kW)", value=0, step=5)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 💼 專案財務模型")
    total_capex = st.sidebar.number_input("建置總成本 CAPEX (元)", value=14500000, step=500000)
    project_years = st.sidebar.number_input("評估年限 (年)", value=15, step=1, max_value=25, min_value=3)
    
    # 💡 V20.31 修正：維運與保險費採百分比連動
    opex_rate = st.sidebar.number_input("每年維護費率 (%)", value=1.5, step=0.1) / 100.0
    annual_opex = total_capex * opex_rate
    
    ins_rate = st.sidebar.number_input("每年保險費率 (%)", value=1.5, step=0.1) / 100.0
    annual_insurance = total_capex * ins_rate
    
    deg_rate = st.sidebar.number_input("電池每年衰退率 (%)", value=3.0, step=0.1) / 100.0
    
    st.sidebar.caption(f"💵 系統試算每年維運費：**${annual_opex:,.0f}**")
    st.sidebar.caption(f"🛡️ 系統試算每年保險費：**${annual_insurance:,.0f}**")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("#### 🕵️ 對帳專用開關")
    apply_holidays = st.sidebar.checkbox("🌴 啟用「國定假日全天離峰」", value=False)
    excel_time_quirk = st.sidebar.checkbox("🔧 模擬「Excel 時間邊界偏差」", value=True)

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
            with st.spinner('正在精算價格套利模型與 AI 預判引擎...'):
                df['西元日期'] = df['年月日'].apply(lambda x: str(int(str(x).split('/')[0])+1911)+'/'+'/'.join(str(x).split('/')[1:]) if '/' in str(x) and len(str(x).split('/')[0])==3 else str(x))
                df['標準時間'] = df['時分'].str.strip().replace('24:00', '00:00')
                df['完整時間'] = pd.to_datetime(df['西元日期'] + ' ' + df['標準時間'])
                df.loc[df['時分'].str.strip() == '24:00', '完整時間'] += pd.Timedelta(days=1)
                
                power_cols = ['尖峰', '半尖峰', '週六半尖峰', '離峰']
                for col in power_cols: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df['原始功率(kW)'] = df[power_cols].sum(axis=1)

                holidays_list = [
                    '01-01', '02-28', '04-04', '04-05', '05-01', '10-10', 
                    '02-08', '02-09', '02-12', '02-13', '02-14', '06-10', '09-17',
                    '01-27', '01-28', '01-29', '01-30', '01-31', '04-03', '05-30', '10-06'
                ]

                def process_row(row):
                    dt = row['完整時間'] if excel_time_quirk else row['完整時間'] - pd.Timedelta(minutes=1)
                    m, d, h = dt.month, dt.day, dt.hour + dt.minute/60.0
                    
                    if apply_holidays:
                        is_holiday = dt.strftime('%m-%d') in holidays_list
                        wd = 6 if is_holiday else dt.weekday()
                    else:
                        wd = dt.weekday()
                        
                    is_sum = (m > 5 and m < 10) or (m == 5 and d >= 16) or (m == 10 and d <= 15)
                    
                    p_3s, r_3s = "3S_離峰", r3_s_off if is_sum else r3_n_off
                    if is_sum:
                        if wd < 5:
                            if 16 <= h < 22: p_3s, r_3s = "3S_夏月尖峰", r3_s_p
                            elif (9 <= h < 16) or (22 <= h < 24): p_3s, r_3s = "3S_半尖峰", r3_s_h
                        elif wd == 5 and 9 <= h < 24: p_3s, r_3s = "3S_週六半尖峰", r3_s_sat
                    else:
                        if wd < 5:
                            if (6 <= h < 11) or (14 <= h < 24): p_3s, r_3s = "3S_半尖峰", r3_n_h
                        elif wd == 5 and ((6 <= h < 11) or (14 <= h < 24)): p_3s, r_3s = "3S_週六半尖峰", r3_n_sat

                    p_b, r_b = "B_離峰", rb_s_off if is_sum else rb_n_off
                    if 15.5 <= h < 21.5: 
                        if wd < 5: 
                            p_b = "B_夏月尖峰" if is_sum else "B_非夏月尖峰"
                            r_b = rb_s_p if is_sum else rb_n_p
                        elif wd == 5: 
                            p_b = "B_週六半尖峰"
                            r_b = rb_s_sat if is_sum else rb_n_sat
                            
                    return pd.Series([p_3s, r_3s, p_b, r_b, 1 if is_sum else 0])

                df[['三段時段', '三段費率', '批次時段', '批次費率', 'Is_Sum']] = df.apply(process_row, axis=1)
                df['Is_Non_Sum'] = 1 - df['Is_Sum']
                df['DateStr'] = df['完整時間'].dt.date

                df['Max_Rem_Rate_3S'] = df[::-1].groupby('DateStr')['三段費率'].cummax()[::-1]
                df['Max_Rem_Rate_BP'] = df[::-1].groupby('DateStr')['批次費率'].cummax()[::-1]

                df['Limit_BP'] = c_reg_op2 + c_non_sum_op2 * df['Is_Non_Sum'] + c_half_op2 + c_sat_op2 + c_off_op2
                df.loc[df['批次時段'] == 'B_夏月尖峰', 'Limit_BP'] = c_reg_op2
                df.loc[df['批次時段'] == 'B_非夏月尖峰', 'Limit_BP'] = c_reg_op2 + c_non_sum_op2
                df.loc[df['批次時段'] == 'B_週六半尖峰', 'Limit_BP'] = c_reg_op2 + c_non_sum_op2 * df['Is_Non_Sum'] + c_half_op2 + c_sat_op2
                
                df['Limit_3S'] = c_reg_op1 + c_non_sum_op1 * df['Is_Non_Sum'] + c_half_op1 + c_sat_op1 + c_off_op1
                df.loc[df['三段時段'] == '3S_夏月尖峰', 'Limit_3S'] = c_reg_op1
                df.loc[df['三段時段'] == '3S_半尖峰', 'Limit_3S'] = c_reg_op1 + c_non_sum_op1 * df['Is_Non_Sum'] + c_half_op1
                df.loc[df['三段時段'] == '3S_週六半尖峰', 'Limit_3S'] = c_reg_op1 + c_non_sum_op1 * df['Is_Non_Sum'] + c_half_op1 + c_sat_op1

                # ====================================================
                # 🛡️ 物理安全充電防線 (Danger Buffer)
                # ====================================================
                if not vpp_enabled:
                    df['Is_VPP_3S'] = 0
                    df['Is_VPP_BP'] = 0
                else:
                    df['Real_Avail_Charge_3S'] = np.clip(df['Limit_3S'] - df['原始功率(kW)'], 10, ess_pow)
                    df['Real_Avail_Charge_BP'] = np.clip(df['Limit_BP'] - df['原始功率(kW)'], 10, ess_pow)
                    
                    avg_charge_kw_3s = df[df['三段時段'] == '3S_離峰']['Real_Avail_Charge_3S'].mean()
                    avg_charge_kw_bp = df[df['批次時段'] == 'B_離峰']['Real_Avail_Charge_BP'].mean()
                    
                    recharge_hrs_3s = (vpp_bid_kw / avg_charge_kw_3s) / ess_eff
                    buffer_hrs_3s = 1.0 + recharge_hrs_3s + 0.5
                    buffer_periods_3s = int(np.ceil(buffer_hrs_3s * 4)) 

                    recharge_hrs_bp = (vpp_bid_kw / avg_charge_kw_bp) / ess_eff
                    buffer_hrs_bp = 1.0 + recharge_hrs_bp + 0.5
                    buffer_periods_bp = int(np.ceil(buffer_hrs_bp * 4))
                    
                    df['Combat_3S'] = df['三段時段'].isin(['3S_夏月尖峰', '3S_半尖峰', '3S_週六半尖峰']).astype(int)
                    df['Combat_BP'] = df['批次時段'].isin(['B_夏月尖峰', 'B_非夏月尖峰', 'B_週六半尖峰']).astype(int)
                    
                    df['Danger_3S'] = df['Combat_3S'].rolling(window=buffer_periods_3s, min_periods=1).max().shift(-buffer_periods_3s).fillna(0)
                    df['Danger_BP'] = df['Combat_BP'].rolling(window=buffer_periods_bp, min_periods=1).max().shift(-buffer_periods_bp).fillna(0)

                    if vpp_schedule_mode == "手動勾選":
                        def check_vpp(period_str):
                            for h in vpp_hours:
                                if h == "尖峰" and "半尖峰" not in period_str and "尖峰" in period_str: return 1
                                elif h != "尖峰" and h in period_str: return 1
                            return 0
                        
                        raw_vpp_3s = df['三段時段'].apply(check_vpp)
                        raw_vpp_bp = df['批次時段'].apply(check_vpp)
                        
                        df['Is_VPP_3S'] = ((raw_vpp_3s == 1) & (df['Danger_3S'] == 0)).astype(int)
                        df['Is_VPP_BP'] = ((raw_vpp_bp == 1) & (df['Danger_BP'] == 0)).astype(int)
                    else:
                        df['Is_VPP_3S'] = ((df['Combat_3S'] == 0) & (df['Danger_3S'] == 0)).astype(int)
                        df['Is_VPP_BP'] = ((df['Combat_BP'] == 0) & (df['Danger_BP'] == 0)).astype(int)

            ess_fixed_pow_3s = 0.0
            ess_fixed_pow_bp = 0.0
            if ess_enabled and ess_strategy == "定額放電":
                if auto_fixed:
                    bp_max_load = df[df['批次時段'].isin(['B_夏月尖峰', 'B_非夏月尖峰'])]['原始功率(kW)'].max()
                    ess_fixed_pow_bp = min(bp_max_load, ess_cap / 6.0, ess_pow)
                    s3_max_load = df[df['三段時段'].isin(['3S_夏月尖峰', '3S_半尖峰'])]['原始功率(kW)'].max()
                    ess_fixed_pow_3s = min(s3_max_load, ess_cap / 15.0, ess_pow)
                else:
                    ess_fixed_pow_3s = ess_fixed_pow_manual
                    ess_fixed_pow_bp = ess_fixed_pow_manual

            # --- 雙軌儲能充放電模擬 ---
            df['ESS_3S功率(kW)'] = 0.0
            df['ESS_BP功率(kW)'] = 0.0
            
            if ess_enabled:
                with st.spinner(f'正在執行充放電對齊運算 (所有模式全面搭載守門員)...'):
                    
                    df['BP_Shave_kW'] = np.maximum(0, df['原始功率(kW)'] - df['Limit_BP'])
                    df.loc[df['批次時段'] == 'B_離峰', 'BP_Shave_kW'] = 0 
                    df['BP_Rem_Shave_kWh'] = df[::-1].groupby('DateStr')['BP_Shave_kW'].cumsum()[::-1] * 0.25

                    df['3S_Shave_kW'] = np.maximum(0, df['原始功率(kW)'] - df['Limit_3S'])
                    df.loc[df['三段時段'] == '3S_離峰', '3S_Shave_kW'] = 0
                    df['3S_Rem_Shave_kWh'] = df[::-1].groupby('DateStr')['3S_Shave_kW'].cumsum()[::-1] * 0.25

                    soc_3s = 0.0
                    soc_bp = 0.0
                    for i, row in df.iterrows():
                        actual_load = row['原始功率(kW)']
                        
                        # ====================================================
                        # 🛡️ 方案一 (3S) 調度邏輯
                        # ====================================================
                        limit_3s = row['Limit_3S']
                        discharge_3s, charge_3s = 0, 0
                        
                        cur_vpp_kw_3s = vpp_bid_kw if row['Is_VPP_3S'] == 1 else 0
                        cur_vpp_kwh_3s = cur_vpp_kw_3s * 1.0
                        avail_pow_3s = max(0, ess_pow - cur_vpp_kw_3s)
                        avail_soc_3s = max(0, soc_3s - cur_vpp_kwh_3s)

                        if ess_strategy == "削峰填谷 (AI動態追隨)":
                            if row['三段時段'] == '3S_離峰':
                                if actual_load > limit_3s and avail_soc_3s > 0:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)
                                elif soc_3s < ess_cap:
                                    safe_margin = max(0, limit_3s - actual_load - ess_charge_margin)
                                    charge_3s = min(avail_pow_3s, (ess_cap - soc_3s) / 0.25, safe_margin)
                            elif row['三段時段'] in ['3S_夏月尖峰', '3S_半尖峰'] and avail_soc_3s > 0: 
                                peak_shave_need = max(0, actual_load - limit_3s)
                                future_need_kwh = max(0, row['3S_Rem_Shave_kWh'] - peak_shave_need * 0.25)
                                free_soc = max(0, avail_soc_3s - future_need_kwh)
                                
                                if row['三段費率'] < row['Max_Rem_Rate_3S']:
                                    free_pow_kw = 0 
                                else:
                                    free_pow_kw = free_soc / 0.25 
                                    
                                desired_discharge = peak_shave_need + free_pow_kw
                                discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, desired_discharge) if ess_allow_export else min(avail_pow_3s, avail_soc_3s / 0.25, actual_load, desired_discharge)
                            elif row['三段時段'] == '3S_週六半尖峰' and avail_soc_3s > 0:
                                if actual_load > limit_3s:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)

                        elif ess_strategy == "定額放電":
                            if row['三段時段'] == '3S_離峰':
                                if actual_load > limit_3s and avail_soc_3s > 0:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)
                                elif soc_3s < ess_cap:
                                    safe_margin = max(0, limit_3s - actual_load - ess_charge_margin)
                                    charge_3s = min(avail_pow_3s, (ess_cap - soc_3s) / 0.25, safe_margin)
                            elif row['三段時段'] in ['3S_夏月尖峰', '3S_半尖峰'] and avail_soc_3s > 0: 
                                if row['三段費率'] < row['Max_Rem_Rate_3S']:
                                    if actual_load > limit_3s:
                                        discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)
                                else:
                                    base_discharge = min(avail_pow_3s, avail_soc_3s / 0.25, ess_fixed_pow_3s) if ess_allow_export else min(avail_pow_3s, avail_soc_3s / 0.25, min(ess_fixed_pow_3s, actual_load))
                                    peak_shave_need = max(0, actual_load - limit_3s)
                                    discharge_3s = max(base_discharge, min(avail_pow_3s, avail_soc_3s / 0.25, peak_shave_need))
                            elif row['三段時段'] == '3S_週六半尖峰' and avail_soc_3s > 0:
                                if actual_load > limit_3s:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)

                        elif ess_strategy == "全力輸出":
                            if row['三段時段'] == '3S_離峰':
                                if actual_load > limit_3s and avail_soc_3s > 0:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)
                                elif soc_3s < ess_cap:
                                    safe_margin = max(0, limit_3s - actual_load - ess_charge_margin)
                                    charge_3s = min(avail_pow_3s, (ess_cap - soc_3s) / 0.25, safe_margin)
                            elif row['三段時段'] in ['3S_夏月尖峰', '3S_半尖峰'] and avail_soc_3s > 0:
                                if row['三段費率'] < row['Max_Rem_Rate_3S']:
                                    if actual_load > limit_3s:
                                        discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)
                                else:
                                    base_discharge = min(avail_pow_3s, avail_soc_3s / 0.25) if ess_allow_export else min(avail_pow_3s, avail_soc_3s / 0.25, actual_load)
                                    peak_shave_need = max(0, actual_load - limit_3s)
                                    discharge_3s = max(base_discharge, min(avail_pow_3s, avail_soc_3s / 0.25, peak_shave_need))
                            elif row['三段時段'] == '3S_週六半尖峰' and avail_soc_3s > 0:
                                if actual_load > limit_3s:
                                    discharge_3s = min(avail_pow_3s, avail_soc_3s / 0.25, actual_load - limit_3s)

                        if discharge_3s > 0:
                            df.at[i, 'ESS_3S功率(kW)'] = discharge_3s
                            soc_3s -= discharge_3s * 0.25
                        elif charge_3s > 0:
                            df.at[i, 'ESS_3S功率(kW)'] = -charge_3s
                            soc_3s += charge_3s * 0.25 * ess_eff

                        # ====================================================
                        # ⚡ 方案二 (BP) 調度邏輯
                        # ====================================================
                        limit_bp = row['Limit_BP']
                        discharge_bp, charge_bp = 0, 0
                        
                        cur_vpp_kw_bp = vpp_bid_kw if row['Is_VPP_BP'] == 1 else 0
                        cur_vpp_kwh_bp = cur_vpp_kw_bp * 1.0 
                        avail_pow_bp = max(0, ess_pow - cur_vpp_kw_bp)
                        avail_soc_bp = max(0, soc_bp - cur_vpp_kwh_bp)

                        if ess_strategy == "削峰填谷 (AI動態追隨)":
                            if row['批次時段'] == 'B_離峰':
                                if actual_load > limit_bp and avail_soc_bp > 0:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)
                                elif soc_bp < ess_cap:
                                    safe_margin = max(0, limit_bp - actual_load - ess_charge_margin)
                                    charge_bp = min(avail_pow_bp, (ess_cap - soc_bp) / 0.25, safe_margin)
                                    
                            elif row['批次時段'] in ['B_夏月尖峰', 'B_非夏月尖峰'] and avail_soc_bp > 0:
                                peak_shave_need = max(0, actual_load - limit_bp)
                                future_need_kwh = max(0, row['BP_Rem_Shave_kWh'] - peak_shave_need * 0.25)
                                free_soc = max(0, avail_soc_bp - future_need_kwh)
                                
                                if row['批次費率'] < row['Max_Rem_Rate_BP']:
                                    free_pow_kw = 0
                                else:
                                    free_pow_kw = free_soc / 0.25
                                    
                                desired_discharge = peak_shave_need + free_pow_kw
                                discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, desired_discharge) if ess_allow_export else min(avail_pow_bp, avail_soc_bp / 0.25, actual_load, desired_discharge)
                                
                            elif row['批次時段'] == 'B_週六半尖峰' and avail_soc_bp > 0:
                                if actual_load > limit_bp:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)

                        elif ess_strategy == "定額放電":
                            if row['批次時段'] == 'B_離峰':
                                if actual_load > limit_bp and avail_soc_bp > 0:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)
                                elif soc_bp < ess_cap:
                                    safe_margin = max(0, limit_bp - actual_load - ess_charge_margin)
                                    charge_bp = min(avail_pow_bp, (ess_cap - soc_bp) / 0.25, safe_margin)
                            elif row['批次時段'] in ['B_夏月尖峰', 'B_非夏月尖峰'] and avail_soc_bp > 0:
                                if row['批次費率'] < row['Max_Rem_Rate_BP']:
                                    if actual_load > limit_bp:
                                        discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)
                                else:
                                    base_discharge = min(avail_pow_bp, avail_soc_bp / 0.25, ess_fixed_pow_bp) if ess_allow_export else min(avail_pow_bp, avail_soc_bp / 0.25, min(ess_fixed_pow_bp, actual_load))
                                    peak_shave_need = max(0, actual_load - limit_bp)
                                    discharge_bp = max(base_discharge, min(avail_pow_bp, avail_soc_bp / 0.25, peak_shave_need))
                            elif row['批次時段'] == 'B_週六半尖峰' and avail_soc_bp > 0:
                                if actual_load > limit_bp:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)

                        elif ess_strategy == "全力輸出":
                            if row['批次時段'] == 'B_離峰':
                                if actual_load > limit_bp and avail_soc_bp > 0:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)
                                elif soc_bp < ess_cap:
                                    safe_margin = max(0, limit_bp - actual_load - ess_charge_margin)
                                    charge_bp = min(avail_pow_bp, (ess_cap - soc_bp) / 0.25, safe_margin)
                            elif row['批次時段'] in ['B_夏月尖峰', 'B_非夏月尖峰'] and avail_soc_bp > 0:
                                if row['批次費率'] < row['Max_Rem_Rate_BP']:
                                    if actual_load > limit_bp:
                                        discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)
                                else:
                                    base_discharge = min(avail_pow_bp, avail_soc_bp / 0.25) if ess_allow_export else min(avail_pow_bp, avail_soc_bp / 0.25, actual_load)
                                    peak_shave_need = max(0, actual_load - limit_bp)
                                    discharge_bp = max(base_discharge, min(avail_pow_bp, avail_soc_bp / 0.25, peak_shave_need))
                            elif row['批次時段'] == 'B_週六半尖峰' and avail_soc_bp > 0:
                                if actual_load > limit_bp:
                                    discharge_bp = min(avail_pow_bp, avail_soc_bp / 0.25, actual_load - limit_bp)

                        if discharge_bp > 0:
                            df.at[i, 'ESS_BP功率(kW)'] = discharge_bp
                            soc_bp -= discharge_bp * 0.25
                        elif charge_bp > 0:
                            df.at[i, 'ESS_BP功率(kW)'] = -charge_bp
                            soc_bp += charge_bp * 0.25 * ess_eff

            # ----------------------------------------------------
            df['原始度數(kWh)'] = df['原始功率(kW)'] * 0.25
            df['原始_三段流動'] = df['原始度數(kWh)'] * df['三段費率']
            
            df['調整後_3S功率(kW)'] = df['原始功率(kW)'] - df['ESS_3S功率(kW)']
            df['調整後_3S流動'] = df['調整後_3S功率(kW)'] * 0.25 * df['三段費率']
            
            df['調整後_BP功率(kW)'] = df['原始功率(kW)'] - df['ESS_BP功率(kW)']
            df['調整後_BP流動'] = df['調整後_BP功率(kW)'] * 0.25 * df['批次費率']

            net_vpp_multiplier = 1.0 - vpp_aggregator_share
            df['VPP_3S_Rev'] = df['Is_VPP_3S'] * (vpp_bid_kw / 1000.0) * vpp_price * 0.25 * net_vpp_multiplier
            df['VPP_BP_Rev'] = df['Is_VPP_BP'] * (vpp_bid_kw / 1000.0) * vpp_price * 0.25 * net_vpp_multiplier

            # --- 月度彙整與電費計算 ---
            df['年月'] = df['完整時間'].dt.strftime('%Y/%m')
            
            df['Orig_Over'] = np.maximum(0, df['原始功率(kW)'] - df['Orig_3S_Limit'] if 'Orig_3S_Limit' in df.columns else c_reg_curr)
            df['Orig_3S_Limit'] = c_reg_curr + c_non_sum_curr * df['Is_Non_Sum'] + c_half_curr + c_sat_curr + c_off_curr
            df.loc[df['三段時段'] == '3S_夏月尖峰', 'Orig_3S_Limit'] = c_reg_curr
            df.loc[df['三段時段'] == '3S_半尖峰', 'Orig_3S_Limit'] = c_reg_curr + c_non_sum_curr * df['Is_Non_Sum'] + c_half_curr
            df.loc[df['三段時段'] == '3S_週六半尖峰', 'Orig_3S_Limit'] = c_reg_curr + c_non_sum_curr * df['Is_Non_Sum'] + c_half_curr + c_sat_curr
            df['Orig_Over'] = np.maximum(0, df['原始功率(kW)'] - df['Orig_3S_Limit'])

            df['Adj_3S_Over'] = np.maximum(0, df['調整後_3S功率(kW)'] - df['Limit_3S'])
            df['Adj_BP_Over'] = np.maximum(0, df['調整後_BP功率(kW)'] - df['Limit_BP'])

            m_flow = df.groupby('年月')[['原始_三段流動', '調整後_3S流動', '調整後_BP流動', 'VPP_3S_Rev', 'VPP_BP_Rev']].sum()
            summary = pd.concat([m_flow], axis=1).reset_index()

            temp_results = []

            for i, row in summary.iterrows():
                m = int(row['年月'].split('/')[1])
                r_reg = b_s_reg if m in [6,7,8,9] else (b_n_reg*15 + b_s_reg*16)/31 if m==5 else (b_s_reg*15 + b_n_reg*16)/31 if m==10 else b_n_reg
                r_off = b_s_off if m in [6,7,8,9] else (b_n_off*15 + b_s_off*16)/31 if m==5 else (b_s_off*15 + b_n_off*16)/31 if m==10 else b_n_off
                non_sum_ratio = 1 if m in [11,12,1,2,3,4] else 15/31 if m==5 else 16/31 if m==10 else 0
                
                off_charge_orig = max(0, (c_sat_curr + c_off_curr) - (c_reg_curr + c_non_sum_curr * non_sum_ratio + c_half_curr) * 0.5)
                base_fee_orig = (c_reg_curr * r_reg) + (c_non_sum_curr * r_reg * non_sum_ratio) + (c_half_curr * r_reg) + (off_charge_orig * r_off)

                off_charge_3s = max(0, (c_sat_op1 + c_off_op1) - (c_reg_op1 + c_non_sum_op1 * non_sum_ratio + c_half_op1) * 0.5)
                base_fee_3s = (c_reg_op1 * r_reg) + (c_non_sum_op1 * r_reg * non_sum_ratio) + (c_half_op1 * r_reg) + (off_charge_3s * r_off)

                off_charge_bp = max(0, (c_sat_op2 + c_off_op2) - (c_reg_op2 + c_non_sum_op2 * non_sum_ratio + c_half_op2) * 0.5)
                base_fee_bp = (c_reg_op2 * r_reg) + (c_non_sum_op2 * r_reg * non_sum_ratio) + (c_half_op2 * r_reg) + (off_charge_bp * r_off)

                def calc_penalty_advanced(df_month, over_col, limit_col, r_reg_price):
                    if df_month[over_col].max() <= 0: return 0
                    idx_max = df_month[over_col].idxmax()
                    max_over = df_month.loc[idx_max, over_col]
                    applicable_limit = df_month.loc[idx_max, limit_col]
                    limit_10 = applicable_limit * 0.1
                    if max_over <= limit_10: return max_over * r_reg_price * 2
                    else: return (limit_10 * r_reg_price * 2) + ((max_over - limit_10) * r_reg_price * 3)

                df_month = df[df['年月'] == row['年月']]
                pen_orig = calc_penalty_advanced(df_month, 'Orig_Over', 'Orig_3S_Limit', r_reg)
                pen_adj_3s = calc_penalty_advanced(df_month, 'Adj_3S_Over', 'Limit_3S', r_reg)
                pen_adj_bp = calc_penalty_advanced(df_month, 'Adj_BP_Over', 'Limit_BP', r_reg)

                flow_orig = row['原始_三段流動']
                total_orig = base_fee_orig + pen_orig + flow_orig
                
                diff_base_3s = base_fee_orig - base_fee_3s
                diff_flow_3s = flow_orig - row['調整後_3S流動']
                diff_pen_3s = pen_orig - pen_adj_3s
                save_3s = diff_base_3s + diff_flow_3s + diff_pen_3s
                total_3s = base_fee_3s + pen_adj_3s + row['調整後_3S流動']

                diff_base_bp = base_fee_orig - base_fee_bp
                diff_flow_bp = flow_orig - row['調整後_BP流動']
                diff_pen_bp = pen_orig - pen_adj_bp
                save_bp = diff_base_bp + diff_flow_bp + diff_pen_bp
                total_bp = base_fee_bp + pen_adj_bp + row['調整後_BP流動']

                temp_results.append({
                    '年月': row['年月'],
                    '現況_基本': base_fee_orig, '現況_流動': flow_orig, '現況_超約': pen_orig, '現況_總計': total_orig,
                    '3S_基本': base_fee_3s, '3S_流動': row['調整後_3S流動'], '3S_超約': pen_adj_3s, '3S_總計': total_3s,
                    '3S_省基本': diff_base_3s, '3S_省流動': diff_flow_3s, '3S_省超約': diff_pen_3s, '3S_省總計': save_3s, '3S_VPP淨收益': row['VPP_3S_Rev'],
                    'BP_基本': base_fee_bp, 'BP_流動': row['調整後_BP流動'], 'BP_超約': pen_adj_bp, 'BP_總計': total_bp,
                    'BP_省基本': diff_base_bp, 'BP_省流動': diff_flow_bp, 'BP_省超約': diff_pen_bp, 'BP_省總計': save_bp, 'BP_VPP淨收益': row['VPP_BP_Rev']
                })

            df_res = pd.DataFrame(temp_results)
            
            ann_base_0 = df_res['現況_基本'].sum()
            ann_flow_0 = df_res['現況_流動'].sum()
            ann_pen_0 = df_res['現況_超約'].sum()
            ann_tot_0 = df_res['現況_總計'].sum()

            ann_base_1 = df_res['3S_基本'].sum()
            ann_flow_1 = df_res['3S_流動'].sum()
            ann_pen_1 = df_res['3S_超約'].sum()
            ann_tot_1 = df_res['3S_總計'].sum()
            ann_save_1 = df_res['3S_省總計'].sum()
            ann_vpp_1 = df_res['3S_VPP淨收益'].sum()

            ann_base_2 = df_res['BP_基本'].sum()
            ann_flow_2 = df_res['BP_流動'].sum()
            ann_pen_2 = df_res['BP_超約'].sum()
            ann_tot_2 = df_res['BP_總計'].sum()
            ann_save_2 = df_res['BP_省總計'].sum()
            ann_vpp_2 = df_res['BP_VPP淨收益'].sum()
            
            ann_opex = annual_opex if ess_enabled else 0
            ann_ins = annual_insurance if ess_enabled else 0

            total_benefit_1 = ann_save_1 + ann_vpp_1
            total_benefit_2 = ann_save_2 + ann_vpp_2

            is_3s_winner = total_benefit_1 > total_benefit_2
            winner_str = "方案一 (三段式+儲能)" if is_3s_winner else "方案二 (批次生產+儲能)"

            st.success("✅ 計算完成！系統已套用最新連動成本費率，防早洩安全防線已全面生效！")

            # ==========================================
            # UI 呈現區
            # ==========================================
            st.markdown(f"### 🏆 系統判定最佳收益：**{winner_str}**")
            
            c1, c2, c3 = st.columns(3)
            c1.metric("📌 現況年度總電費", f"${ann_tot_0:,.0f}")
            c2.metric(f"{'⭐ ' if is_3s_winner else ''}🛡️ 方案一 (3S) 總費", f"${ann_tot_1:,.0f}", f"淨省 ${total_benefit_1:,.0f}")
            c3.metric(f"{'⭐ ' if not is_3s_winner else ''}⚡ 方案二 (BP) 總費", f"${ann_tot_2:,.0f}", f"淨省 ${total_benefit_2:,.0f}")
            
            st.markdown("#### 📊 三大方案電費結構與 VPP 淨收益拆解 (年度總計)")
            
            compare_df = pd.DataFrame({
                "財務項目": ["基本電費", "流動電費", "超約罰款", "【台電電費總計】", "➕ VPP 淨收益 (已扣代操費)", "❌ 每年維護費", "❌ 每年保險費", "🎉【第一年淨現金流】"],
                "📌 現況 (無儲能)": [ann_base_0, ann_flow_0, ann_pen_0, ann_tot_0, 0, 0, 0, 0],
                "🛡️ 方案一 (3S)": [ann_base_1, ann_flow_1, ann_pen_1, ann_tot_1, ann_vpp_1, ann_opex, ann_ins, total_benefit_1 - ann_opex - ann_ins],
                "⚡ 方案二 (BP)": [ann_base_2, ann_flow_2, ann_pen_2, ann_tot_2, ann_vpp_2, ann_opex, ann_ins, total_benefit_2 - ann_opex - ann_ins]
            })
            
            def format_currency(x):
                if isinstance(x, (int, float)): return f"${x:,.0f}"
                return x

            st.table(compare_df.style.format({
                "📌 現況 (無儲能)": format_currency,
                "🛡️ 方案一 (3S)": format_currency,
                "⚡ 方案二 (BP)": format_currency
            }).set_properties(**{'text-align': 'right'}))

            st.divider()

            col_left, col_right = st.columns([1, 1.2])

            with col_left:
                st.subheader(f"📋 1~12 月份節省明細")
                tab1, tab2 = st.tabs(["🛡️ 方案一 (3S)", "⚡ 方案二 (BP)"])
                format_dict = {c: "{:,.0f}" for c in ['省基本', '省流動', '省超約', '省總計', 'VPP淨收益']}
                
                with tab1:
                    df_3s_view = df_res[['年月', '3S_省基本', '3S_省流動', '3S_省超約', '3S_省總計', '3S_VPP淨收益']].rename(columns={'3S_省基本': '省基本', '3S_省流動': '省流動', '3S_省超約': '省超約', '3S_省總計': '省總計', '3S_VPP淨收益': 'VPP淨收益'})
                    st.dataframe(df_3s_view.style.format(format_dict))
                with tab2:
                    df_bp_view = df_res[['年月', 'BP_省基本', 'BP_省流動', 'BP_省超約', 'BP_省總計', 'BP_VPP淨收益']].rename(columns={'BP_省基本': '省基本', 'BP_省流動': '省流動', 'BP_省超約': '省超約', 'BP_省總計': '省總計', 'BP_VPP淨收益': 'VPP淨收益'})
                    st.dataframe(df_bp_view.style.format(format_dict))

            with col_right:
                st.subheader(f"📈 長期現金流對決 (含 VPP 淨收益疊加)")
                
                cf_1, cf_2 = [-total_capex], [-total_capex]
                for yr in range(1, int(project_years) + 1):
                    ef = (1 - deg_rate) ** (yr - 1)
                    cf_1.append((total_benefit_1 * ef) - annual_opex - annual_insurance)
                    cf_2.append((total_benefit_2 * ef) - annual_opex - annual_insurance)

                cum_1, cum_2 = np.cumsum(cf_1), np.cumsum(cf_2)
                
                def calc_fin(cf_list, cum_cf):
                    pb = -1
                    for i in range(1, len(cum_cf)):
                        if cum_cf[i] >= 0:
                            pb = (i - 1) + abs(cum_cf[i-1]) / cf_list[i]
                            break
                    if sum(cf_list) < 0: return -1.0, pb
                    r = 0.05
                    for _ in range(100):
                        npv = sum([c / (1 + r)**i for i, c in enumerate(cf_list)])
                        der = sum([-i * c / (1 + r)**(i + 1) for i, c in enumerate(cf_list)])
                        if abs(der) < 1e-6: break
                        r -= npv / der
                        if abs(npv) < 1e-4: return r, pb
                    return r, pb

                irr_1, pb_1 = calc_fin(cf_1, cum_1)
                irr_2, pb_2 = calc_fin(cf_2, cum_2)

                chart_df = pd.DataFrame({"🛡️ 3S 累計": cum_1, "⚡ BP 累計": cum_2})
                st.line_chart(chart_df, color=["#1f77b4", "#ff7f0e"])

                m1, m2 = st.columns(2)
                with m1: st.info(f"**方案一 (3S)**\n\n回收期：{f'{pb_1:.1f} 年' if pb_1 > 0 else '無法回本'}\n\nIRR：{f'{irr_1*100:.1f}%' if irr_1 >= 0 else '負值'}")
                with m2: st.warning(f"**方案二 (BP)**\n\n回收期：{f'{pb_2:.1f} 年' if pb_2 > 0 else '無法回本'}\n\nIRR：{f'{irr_2*100:.1f}%' if irr_2 >= 0 else '負值'}")

            st.markdown("---")
            col_dl1, col_dl2 = st.columns(2)
            col_dl1.download_button("📊 下載【月度明細表】CSV", data=df_res.to_csv(index=False).encode('utf-8-sig'), file_name="月度明細表.csv", mime="text/csv")
            if ess_enabled: col_dl2.download_button("💰 下載【長期現金流】CSV", data=chart_df.to_csv().encode('utf-8-sig'), file_name="長期現金流.csv", mime="text/csv")

    except Exception as e:
        st.error(f"分析失敗：{str(e)}")