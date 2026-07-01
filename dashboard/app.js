/**
 * NeuraCoin Dashboard - Wallet Connect
 *
 * Implements the wallet connection modal behavior for the NeuraCoin dashboard.
 * Detects an injected EIP-1193 provider (window.ethereum), requests account
 * access, and surfaces the connected address in the UI.
 *
 * Wire this file into dashboard/index.html with:
 *   <script src="app.js" defer></script>
 * placed just before the closing </body> tag.
 */

(function () {
  'use strict';

  // ---------------------------------------------------------------------------
  // DOM references
  // ---------------------------------------------------------------------------
  const walletBtn = document.getElementById('walletBtn') || document.querySelector('.wallet-btn');
  const modal = document.getElementById('modal');
  const connectBtn = document.getElementById('connect-wallet') || document.querySelector('.connect-wallet');
  const closeBtn = document.getElementById('modal-close') || (modal && modal.querySelector('.close'));

  // Local state
  let connectedAccount = null;

  // ---------------------------------------------------------------------------
  // Helpers
  // ---------------------------------------------------------------------------

  /**
   * Shorten an Ethereum address for display: 0x1234…abcd
   * @param {string} addr
   * @returns {string}
   */
  function shortenAddress(addr) {
    if (!addr || typeof addr !== 'string') return '';
    if (addr.length <= 10) return addr;
    return addr.slice(0, 6) + '…' + addr.slice(-4);
  }

  /**
   * Update the wallet button label based on connection state.
   * @param {string|null} account
   */
  function updateWalletButton(account) {
    if (!walletBtn) return;
    if (account) {
      walletBtn.textContent = shortenAddress(account);
      walletBtn.setAttribute('title', account);
      walletBtn.classList.add('connected');
    } else {
      walletBtn.textContent = 'Connect Wallet';
      walletBtn.removeAttribute('title');
      walletBtn.classList.remove('connected');
    }
  }

  function openModal() {
    if (!modal) return;
    modal.style.display = 'flex';
    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
  }

  function closeModal() {
    if (!modal) return;
    modal.style.display = 'none';
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
  }

  /**
   * Render a status message inside the modal (creates a slot if missing).
   * @param {string} message
   * @param {'info'|'error'|'success'} [level]
   */
  function setModalStatus(message, level) {
    if (!modal) return;
    let status = modal.querySelector('.modal-status');
    if (!status) {
      status = document.createElement('p');
      status.className = 'modal-status';
      modal.appendChild(status);
    }
    status.textContent = message || '';
    status.dataset.level = level || 'info';
  }

  // ---------------------------------------------------------------------------
  // Wallet integration (EIP-1193)
  // ---------------------------------------------------------------------------

  /**
   * Detect an injected Ethereum provider.
   * @returns {object|null}
   */
  function getProvider() {
    if (typeof window !== 'undefined' && window.ethereum) {
      return window.ethereum;
    }
    return null;
  }

  /**
   * Request accounts from the injected provider.
   * @returns {Promise<string|null>}
   */
  async function requestAccounts() {
    const provider = getProvider();
    if (!provider) {
      setModalStatus(
        'No Ethereum wallet detected. Please install MetaMask or a compatible wallet.',
        'error'
      );
      return null;
    }

    try {
      setModalStatus('Requesting wallet accounts…', 'info');
      const accounts = await provider.request({ method: 'eth_requestAccounts' });
      if (!Array.isArray(accounts) || accounts.length === 0) {
        setModalStatus('No accounts returned from wallet.', 'error');
        return null;
      }
      return accounts[0];
    } catch (err) {
      // EIP-1193: 4001 = user rejected request
      if (err && err.code === 4001) {
        setModalStatus('Connection request rejected.', 'error');
      } else {
        const msg = (err && err.message) ? err.message : 'Failed to connect wallet.';
        setModalStatus(msg, 'error');
      }
      return null;
    }
  }

  /**
   * Attempt to silently restore a previous connection (no user prompt).
   */
  async function restoreConnection() {
    const provider = getProvider();
    if (!provider) return;
    try {
      const accounts = await provider.request({ method: 'eth_accounts' });
      if (Array.isArray(accounts) && accounts.length > 0) {
        connectedAccount = accounts[0];
        updateWalletButton(connectedAccount);
      }
    } catch (_) {
      // Silent restore failures are non-fatal.
    }
  }

  /**
   * Bind provider events so the UI reacts to account/chain changes.
   */
  function bindProviderEvents() {
    const provider = getProvider();
    if (!provider || typeof provider.on !== 'function') return;

    provider.on('accountsChanged', (accounts) => {
      if (Array.isArray(accounts) && accounts.length > 0) {
        connectedAccount = accounts[0];
      } else {
        connectedAccount = null;
      }
      updateWalletButton(connectedAccount);
    });

    provider.on('chainChanged', () => {
      // Reload is the officially recommended handling for chain changes.
      window.location.reload();
    });

    provider.on('disconnect', () => {
      connectedAccount = null;
      updateWalletButton(null);
    });
  }

  // ---------------------------------------------------------------------------
  // Event wiring
  // ---------------------------------------------------------------------------

  async function handleWalletBtnClick() {
    // If already connected, toggle the modal for account details.
    if (connectedAccount) {
      setModalStatus('Connected: ' + connectedAccount, 'success');
      openModal();
      return;
    }
    openModal();
    setModalStatus('Click "Connect" to link your wallet.', 'info');
  }

  async function handleConnectClick() {
    const account = await requestAccounts();
    if (account) {
      connectedAccount = account;
      updateWalletButton(connectedAccount);
      setModalStatus('Connected: ' + account, 'success');
      // Auto-close after a brief confirmation delay.
      setTimeout(closeModal, 900);
    }
  }

  function bindUiEvents() {
    if (walletBtn) {
      walletBtn.addEventListener('click', handleWalletBtnClick);
    }
    if (connectBtn) {
      connectBtn.addEventListener('click', handleConnectClick);
    }
    if (closeBtn) {
      closeBtn.addEventListener('click', closeModal);
    }
    // Click outside modal content closes it.
    if (modal) {
      modal.addEventListener('click', (evt) => {
        if (evt.target === modal) closeModal();
      });
    }
    // Escape key closes modal.
    document.addEventListener('keydown', (evt) => {
      if (evt.key === 'Escape') closeModal();
    });
  }

  // ---------------------------------------------------------------------------
  // Bootstrap
  // ---------------------------------------------------------------------------

  function init() {
    bindUiEvents();
    bindProviderEvents();
    updateWalletButton(null);
    // Ensure modal starts hidden.
    closeModal();
    // Try silent restore of a prior session.
    restoreConnection();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
