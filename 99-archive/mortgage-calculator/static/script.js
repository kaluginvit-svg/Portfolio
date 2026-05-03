const form = document.getElementById("calc-form");
const resultsBlock = document.getElementById("results");
const monthlyEl = document.getElementById("monthly");
const totalEl = document.getElementById("total");
const overpaymentEl = document.getElementById("overpayment");
const financedEl = document.getElementById("financed");
const monthsEl = document.getElementById("months");
const submitBtn = document.getElementById("submit-btn");
const exportBtn = document.getElementById("export-btn");
const installmentBtn = document.getElementById("installment-toggle");
const rateField = document.getElementById("rate-field");
const extraAmountInput = document.getElementById("extra_amount");
const extraMonthInput = document.getElementById("extra_month");
const addExtraBtn = document.getElementById("add-extra");
const extraList = document.getElementById("extra-list");

let extraPayments = [];
let lastPayload = null;
let installmentMode = false;

const moneyInputs = [
  document.getElementById("amount"),
  document.getElementById("down_payment"),
  extraAmountInput,
];

const formatCurrency = (value) =>
  new Intl.NumberFormat("ru-RU", {
    style: "currency",
    currency: "RUB",
    maximumFractionDigits: 0,
  }).format(value);

const parseNumber = (value) => Number(String(value).replace(/\s+/g, "")) || 0;

const formatMoneyInput = (input) => {
  const raw = String(input.value).replace(/[^\d]/g, "");
  if (!raw) {
    input.value = "";
    return;
  }
  const withSpaces = raw.replace(/\B(?=(\d{3})+(?!\d))/g, " ");
  input.value = withSpaces;
};

moneyInputs.forEach((input) => {
  input?.addEventListener("input", () => formatMoneyInput(input));
  if (input) formatMoneyInput(input);
});

installmentBtn.addEventListener("click", () => {
  installmentMode = !installmentMode;
  installmentBtn.classList.toggle("active", installmentMode);
  rateField.classList.toggle("hidden", installmentMode);
  const rateInput = document.getElementById("rate");
  if (installmentMode) {
    rateInput.value = "0";
    rateInput.removeAttribute("required");
  } else {
    rateInput.setAttribute("required", "required");
  }
});

const renderExtraPayments = () => {
  extraList.innerHTML = "";
  if (!extraPayments.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = "Пока нет досрочных платежей";
    extraList.appendChild(li);
    return;
  }

  extraPayments
    .sort((a, b) => a.month - b.month)
    .forEach((item, idx) => {
      const li = document.createElement("li");
      li.innerHTML = `
        <span>Месяц ${item.month}: ${formatCurrency(item.amount)}</span>
        <button type="button" data-idx="${idx}" class="ghost small">×</button>
      `;
      extraList.appendChild(li);
    });

  extraList.querySelectorAll("button").forEach((btn) =>
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.idx);
      extraPayments.splice(idx, 1);
      renderExtraPayments();
    })
  );
};

addExtraBtn.addEventListener("click", () => {
  const amount = parseNumber(extraAmountInput.value);
  const month = Number(extraMonthInput.value);
  if (!amount || !month || month < 1) {
    alert("Введите сумму и месяц для досрочного платежа.");
    return;
  }
  extraPayments.push({ amount, month });
  extraAmountInput.value = "";
  extraMonthInput.value = "";
  renderExtraPayments();
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  submitBtn.classList.add("loading");
  submitBtn.disabled = true;
  exportBtn.disabled = true;

  const repayMode = form.repay_mode.value || "reduce_term";
  const payload = {
    amount: parseNumber(form.amount.value),
    downPayment: parseNumber(form.down_payment.value),
    years: Number(form.years.value),
    rate: installmentMode ? 0 : Number(form.rate.value || 0),
    extraPayments,
    repayMode,
  };

  lastPayload = payload;

  try {
    const response = await fetch("/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const result = await response.json();
    if (!response.ok || !result.success) {
      throw new Error(result.error || "Не удалось выполнить расчет.");
    }

    const { monthlyPayment, totalPaid, overpayment, financedPrincipal, monthsActual } =
      result.data;
    monthlyEl.textContent = formatCurrency(monthlyPayment);
    totalEl.textContent = formatCurrency(totalPaid);
    overpaymentEl.textContent = formatCurrency(overpayment);
    financedEl.textContent = formatCurrency(financedPrincipal);
    monthsEl.textContent = monthsActual;
    resultsBlock.hidden = false;
    exportBtn.disabled = false;
  } catch (error) {
    alert(error.message || "Произошла ошибка. Попробуйте снова.");
  } finally {
    submitBtn.classList.remove("loading");
    submitBtn.disabled = false;
  }
});

exportBtn.addEventListener("click", async () => {
  if (!lastPayload) {
    alert("Сначала выполните расчет.");
    return;
  }
  exportBtn.classList.add("loading");
  exportBtn.disabled = true;
  try {
    const response = await fetch("/export", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastPayload),
    });
    if (!response.ok) {
      throw new Error("Не удалось выгрузить Excel.");
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "schedule.xlsx";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (error) {
    alert(error.message || "Ошибка при выгрузке Excel.");
  } finally {
    exportBtn.classList.remove("loading");
    exportBtn.disabled = false;
  }
});

renderExtraPayments();

