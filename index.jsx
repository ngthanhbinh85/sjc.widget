import { css, run } from "uebersicht";

// 5 phút nạp lại dữ liệu một lần, bạn có thể thay đổi, 
// nhưng không nên sớm hơn 5 phút, đề phòng các dịch vụ chặn.
// Ngoài ra, giá vàng SJC cũng không thay đổi nhanh
export const refreshFrequency = 5 * 60 * 1000;

// Thay đổi đường dẫn python3 cho phù hợp với máy của bạn
export const command = `
  /Library/Frameworks/Python.framework/Versions/3.14/bin/python3 \
  "$HOME/Library/Application Support/Übersicht/widgets/sjc.widget/sjc_price.py"
`;

const formatPrice = value => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return new Intl.NumberFormat("vi-VN").format(number);
};

const formatDecimal = value => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  return new Intl.NumberFormat("vi-VN", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(number);
};

const formatSignedPrice = value => {
  if (value === null || value === undefined || value === "") {
    return "—";
  }

  const number = Number(value);

  if (!Number.isFinite(number)) {
    return "—";
  }

  const sign = number > 0 ? "+" : "";
  return `${sign}${formatPrice(Math.round(number))}`;
};

const refreshData = (event, dispatch) => {
  const button = event.currentTarget;
  button.classList.add(refreshing);

  run(command).then(
    output => dispatch({ type: "UB/COMMAND_RAN", output }),
    error => dispatch({ type: "UB/COMMAND_RAN", error })
  ).then(() => {
    setTimeout(() => button.classList.remove(refreshing), 400);
  });
};

const Header = ({ dispatch }) => (
  <div className={header}>
    <span className={title}>GIÁ VÀNG SJC</span>
    <span
      className={refreshButton}
      title="Làm mới giá"
      onClick={event => refreshData(event, dispatch)}
    >
      &#8635;
    </span>
  </div>
);

export const render = ({ output, error }, dispatch) => {
  if (error) {
    return (
      <div className={container}>
        <Header dispatch={dispatch} />

        <div className={errorText}>
          Không tải được dữ liệu
        </div>

        <div className={debugText}>
          {String(error)}
        </div>
      </div>
    );
  }

  let data;

  try {
    data = JSON.parse((output || "").trim());
  } catch (parseError) {
    return (
      <div className={container}>
        <Header dispatch={dispatch} />

        <div className={errorText}>
          JSON không hợp lệ
        </div>

        <div className={debugText}>
          {output || String(parseError)}
        </div>
      </div>
    );
  }

  if (data.error) {
    return (
      <div className={container}>
        <Header dispatch={dispatch} />

        <div className={errorText}>
          {data.error}
        </div>
      </div>
    );
  }

  const international = data.international_vnd_luong == null
    ? NaN
    : Number(data.international_vnd_luong);
  const premium = data.premium_sell == null
    ? NaN
    : Number(data.premium_sell);

  const buy = Number(data.buy);
  const sell = Number(data.sell);

  const spread =
    Number.isFinite(buy) && Number.isFinite(sell)
      ? sell - buy
      : null;

  return (
    <div className={container}>
      <Header dispatch={dispatch} />

      <div className={product}>
        <span>
          {data.name || "Vàng miếng SJC"} (VND/lượng)
        </span>
        <span>
          Cập nhật:{" "}
          {new Date().toLocaleTimeString("vi-VN", {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </span>
      </div>

      <div className={priceRow}>
        <div>
          <div className={label}>MUA VÀO</div>
          <div className={price}>
            {formatPrice(data.buy)}
          </div>
        </div>

        <div className={rightColumn}>
          <div className={label}>BÁN RA</div>
          <div className={price}>
            {formatPrice(data.sell)}
          </div>
        </div>
      </div>

      <div className={footer}>
        <div className={footerRow}>
          <span>
            Chênh lệch bán - mua:
          </span>
          <span>
            {" "}{spread === null ? "—" : formatPrice(spread)}
          </span>
        </div>
        <div className={footerRow}>
          <span>
            Giá quốc tế quy đổi chưa bao gồm thuế phí: 
          </span>
          <span>{Number.isFinite(international)
              ? formatPrice(Math.round(international))
              : "—"}
          </span>
        </div>
        <div className={footerRow}>
          <span>
            Chênh lệch giá bán SJC - giá quốc tế: 
          </span>
          <span>
            {Number.isFinite(premium)
              ? formatSignedPrice(premium) : "—"}
          </span>
        </div>
        
        <div style={{ height: "3px" }} />

        <div className={footerRow2}>
          <span>XAU/USD: ASK {formatDecimal(data.spot_usd_oz)}</span>
          <span>USD/VND: {formatPrice(data.usd_vnd_sell)}</span>
        </div>
      </div>
    </div>
  );
};

const container = css`
  position: fixed;
  top: 150px;
  left: 15px;

  width: 350px;
  padding: 16px;
  box-sizing: border-box;

  color: rgba(255, 255, 255, 0.96);
  text-shadow:
    1px 1px 2px #000,
    -1px -1px 2px #000,
    1px -1px 2px #000,
    -1px 1px 2px #000,
    0 0 5px rgba(0, 0, 0, 0.9);
  background: rgba(15, 15, 18, 0.28);

  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 16px;

  transform: translateZ(0);
  -webkit-font-smoothing: antialiased;

  font-family:
    -apple-system,
    BlinkMacSystemFont,
    "SF Pro Display",
    sans-serif;
`;

const header = css`
  display: flex;
  align-items: baseline;
  justify-content: space-between;
`;

const title = css`
  font-size: 14px;
  font-weight: 750;
  letter-spacing: 0.8px;
`;

const refreshButton = css`
  padding: 0 2px;
  color: rgb(255, 255, 255);
  font-size: 14px;
  line-height: 1;
  opacity: 0.6;
  cursor: pointer;
  user-select: none;
  transition: transform 0.4s ease, opacity 0.2s ease;

  &:hover {
    opacity: 1;
  }
`;

const refreshing = css`
  transform: rotate(360deg);
`;

const product = css`
  margin-top: 5px;
  font-size: 11px;
  opacity: 0.65;
  display: flex;
  justify-content: space-between;
`;

const priceRow = css`
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
`;

const rightColumn = css`
  text-align: right;
`;

const label = css`
  margin-bottom: 4px;

  font-size: 10px;
  font-weight: 650;
  letter-spacing: 0.7px;
`;

const price = css`
  font-size: 20px;
  font-weight: 720;
  font-variant-numeric: tabular-nums;
`;

const footer = css`
  display: flex;
  flex-direction: column;
  gap: 4px;

  margin-top: 13px;
  padding-top: 9px;

  border-top: 1px solid rgba(255, 255, 255, 0.1);

  font-size: 11px;

`;

const footerRow = css`
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-variant-numeric: tabular-nums;
`;

const footerRow2 = css`
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-variant-numeric: tabular-nums;
  opacity: 0.65;
`;

const errorText = css`
  margin-top: 10px;

  font-size: 12px;
  line-height: 1.4;

  opacity: 0.85;
`;

const debugText = css`
  margin-top: 6px;

  max-width: 100%;
  overflow-wrap: anywhere;

  font-family: "SF Mono", monospace;
  font-size: 9px;
  line-height: 1.4;

  opacity: 0.5;
`;
