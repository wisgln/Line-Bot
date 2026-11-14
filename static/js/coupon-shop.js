(() => {
  'use strict';
  const root = document.getElementById('shop');
  if (!root) return;
  const couponId = root.dataset.couponId;
  const expired = root.dataset.expired === 'true';
  const unitPrice = Number(root.dataset.unitPrice || 0);
  const minSpend = Number(root.dataset.minSpend || 0);
  const quantityUnit = root.dataset.quantityUnit || '件';
  const thresholdHint = document.getElementById('threshold-hint');
  const qtyValue = document.getElementById('quantity-value');
  const qtyHidden = document.getElementById('quantity');
  const dec = document.getElementById('decrease');
  const inc = document.getElementById('increase');
  const complete = document.getElementById('complete');
  const status = document.getElementById('status');
  const money = v => 'NT$ ' + Number(v).toLocaleString('en-US');
  let quantity = 1;
  let requestVersion = 0;
  let busy = false;
  const endpoint = '/api/coupon';

  const refresh = async () => {
    const version = ++requestVersion;
    qtyValue.textContent = String(quantity);
    qtyHidden.value = String(quantity);
    status.textContent = '';
    complete.disabled = true;
    try {
      const resp = await fetch(`${endpoint}/quote/${encodeURIComponent(couponId)}?quantity=${quantity}`, {cache:'no-store'});
      const data = await resp.json();
      if (version !== requestVersion) return;
      if (!resp.ok) throw new Error(data.error || '暫時無法計算，請稍後重試');
      document.getElementById('subtotal').textContent = money(data.original);
      document.getElementById('discount').textContent = '− ' + money(data.discount);
      document.getElementById('total').textContent = money(data.total);
      if (thresholdHint && minSpend > 0 && unitPrice > 0) {
        const shortfall = Math.max(0, minSpend - quantity * unitPrice);
        if (shortfall > 0) {
          const more = Math.ceil(shortfall / unitPrice);
          thresholdHint.textContent = `再選 ${more} ${quantityUnit}，即可符合滿額優惠`;
        } else {
          thresholdHint.textContent = '已達滿額門檻，優惠已列入試算';
        }
        thresholdHint.hidden = false;
      }
    } catch (error) {
      if (version !== requestVersion) return;
      status.textContent = error.message || '無法連線';
    } finally {
      if (version === requestVersion && !expired && !busy && !status.textContent) complete.disabled = false;
    }
  };

  const change = delta => {
    if (busy) return;
    const next = Math.max(1, Math.min(10, quantity + delta));
    if (quantity !== next) { quantity = next; refresh(); }
  };
  dec.addEventListener('click', () => change(-1));
  inc.addEventListener('click', () => change(1));

  complete.addEventListener('click', async () => {
    if (busy || expired) return;
    busy = true;
    complete.disabled = true;
    status.textContent = '';
    try {
      const resp = await fetch(`${endpoint}/complete/${encodeURIComponent(couponId)}`, {
        method:'POST', headers:{'Content-Type':'application/json'},
        body:JSON.stringify({quantity}), cache:'no-store'
      });
      const data = await resp.json();
      if (!resp.ok) throw new Error(data.error || '無法完成體驗，請重試');
      document.getElementById('receipt-name').textContent = data.product_name;
      document.getElementById('receipt-quantity').textContent = String(data.quantity) + ' ' + quantityUnit;
      document.getElementById('receipt-total').textContent = money(data.quote.total);
      const receipt = document.getElementById('receipt');
      receipt.hidden = false;
      receipt.focus();
      receipt.scrollIntoView({behavior:'smooth', block:'start'});
    } catch(error) {
      status.textContent = error.message || '連線失敗';
    } finally {
      busy = false;
      if (!expired) complete.disabled = false;
    }
  });
  document.getElementById('again').addEventListener('click', () => {
    document.getElementById('receipt').hidden = true;
    document.querySelector('.checkout').scrollIntoView({behavior:'smooth',block:'start'});
  });
  if (!expired) refresh();
})();
