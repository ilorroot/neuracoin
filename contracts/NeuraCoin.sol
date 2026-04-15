// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/Pausable.sol";

/**
 * @title NeuraCoin Token (NRC)
 * @notice ERC-20 token for the NeuraCoin decentralized AI compute protocol.
 *         Used for job payment, staking, and governance.
 * @dev Total supply: 1,000,000,000 NRC (1 billion)
 */
contract NeuraCoin is ERC20, Ownable, Pausable {

    // ── Constants ────────────────────────────────────────────────────────────

    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10 ** 18;

    // Allocation buckets (in whole NRC, pre-scaled)
    uint256 public constant COMPUTE_REWARDS_ALLOC = 400_000_000 * 10 ** 18;
    uint256 public constant ECOSYSTEM_ALLOC       = 200_000_000 * 10 ** 18;
    uint256 public constant TEAM_ALLOC            = 200_000_000 * 10 ** 18;
    uint256 public constant PUBLIC_SALE_ALLOC     = 150_000_000 * 10 ** 18;
    uint256 public constant RESERVE_ALLOC         = 50_000_000  * 10 ** 18;

    // ── State ─────────────────────────────────────────────────────────────────

    address public rewardEmitter;       // JobRegistry contract address
    uint256 public totalEmitted;        // Tracks compute rewards emitted so far
    uint256 public totalBurned;         // Tracks total tokens burned

    // ── Events ────────────────────────────────────────────────────────────────

    event RewardEmitterSet(address indexed emitter);
    event ComputeRewardMinted(address indexed provider, uint256 amount);
    event TokenBurned(address indexed burner, uint256 amount);

    // ── Constructor ───────────────────────────────────────────────────────────

    constructor(
        address teamWallet,
        address ecosystemWallet,
        address publicSaleWallet,
        address reserveWallet
    ) ERC20("NeuraCoin", "NRC") Ownable(msg.sender) {
        // Mint fixed allocations at deployment
        _mint(teamWallet,        TEAM_ALLOC);
        _mint(ecosystemWallet,   ECOSYSTEM_ALLOC);
        _mint(publicSaleWallet,  PUBLIC_SALE_ALLOC);
        _mint(reserveWallet,     RESERVE_ALLOC);
        // Compute rewards are minted lazily via emitReward()
    }

    // ── Reward emission ───────────────────────────────────────────────────────

    /**
     * @notice Called by the JobRegistry contract to mint compute rewards.
     * @param provider  Address of the compute provider to reward.
     * @param amount    Amount of NRC to mint (in wei).
     */
    function emitReward(address provider, uint256 amount) external {
        require(msg.sender == rewardEmitter, "NRC: caller is not reward emitter");
        require(totalEmitted + amount <= COMPUTE_REWARDS_ALLOC, "NRC: compute reward pool exhausted");
        totalEmitted += amount;
        _mint(provider, amount);
        emit ComputeRewardMinted(provider, amount);
    }

    // ── Token burning ─────────────────────────────────────────────────────────

    /**
     * @notice Allows token holders to burn their own tokens.
     * @param amount Amount of NRC to burn (in wei).
     */
    function burn(uint256 amount) external {
        require(amount > 0, "NRC: burn amount must be greater than zero");
        _burn(msg.sender, amount);
        totalBurned += amount;
        emit TokenBurned(msg.sender, amount);
    }

    // ── Admin ─────────────────────────────────────────────────────────────────

    /**
     * @notice Sets the reward emitter address (should be the JobRegistry contract).
     * @param emitter Address of the reward emitter contract.
     */
    function setRewardEmitter(address emitter) external onlyOwner {
        require(emitter != address(0), "NRC: invalid emitter address");
        rewardEmitter = emitter;
        emit RewardEmitterSet(emitter);
    }

    /**
     * @notice Pauses all token transfers.
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpauses all token transfers.
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    // ── Pausable hook ─────────────────────────────────────────────────────────

    /**
     * @notice Hook to enforce pause state on token transfers.
     */
    function _update(
        address from,
        address to,
        uint256 amount
    ) internal override whenNotPaused {
        super._update(from, to, amount);
    }
}