// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title DocumentRegistry
/// @notice Hackathon prototype: stores document fingerprints and limited issuer metadata.
/// @dev No PII or document images are stored on-chain.
contract DocumentRegistry {
    bytes32 public constant ISSUER_ROLE = keccak256("ISSUER_ROLE");
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    struct Document {
        string issuer;
        uint256 issuedAt;
        uint256 expiry;
        bool active;
        bool exists;
    }

    mapping(bytes32 => Document) private documents;
    mapping(bytes32 => mapping(address => bool)) private roleMembers;

    address public immutable admin;

    event DocumentRegistered(bytes32 indexed documentHash, string issuer, uint256 expiry, uint256 timestamp);
    event DocumentRevoked(bytes32 indexed documentHash, uint256 timestamp);
    event RoleGranted(bytes32 indexed role, address indexed account);
    event RoleRevoked(bytes32 indexed role, address indexed account);

    modifier onlyAdmin() {
        require(msg.sender == admin, "ADMIN_ONLY");
        _;
    }

    modifier onlyIssuer() {
        require(msg.sender == admin || roleMembers[ISSUER_ROLE][msg.sender], "ISSUER_ONLY");
        _;
    }

    constructor() {
        admin = msg.sender;
        roleMembers[AUDITOR_ROLE][msg.sender] = true;
    }

    function grantIssuer(address account) external onlyAdmin {
        roleMembers[ISSUER_ROLE][account] = true;
        emit RoleGranted(ISSUER_ROLE, account);
    }

    function revokeIssuer(address account) external onlyAdmin {
        roleMembers[ISSUER_ROLE][account] = false;
        emit RoleRevoked(ISSUER_ROLE, account);
    }

    function hasRole(bytes32 role, address account) external view returns (bool) {
        return roleMembers[role][account];
    }

    function registerDocument(
        bytes32 documentHash,
        string calldata issuer,
        uint256 expiry
    ) external onlyIssuer {
        require(documentHash != bytes32(0), "EMPTY_HASH");
        require(!documents[documentHash].exists, "ALREADY_REGISTERED");

        documents[documentHash] = Document({
            issuer: issuer,
            issuedAt: block.timestamp,
            expiry: expiry,
            active: true,
            exists: true
        });

        emit DocumentRegistered(documentHash, issuer, expiry, block.timestamp);
    }

    function revokeDocument(bytes32 documentHash) external onlyIssuer {
        require(documents[documentHash].exists, "NOT_REGISTERED");
        documents[documentHash].active = false;
        emit DocumentRevoked(documentHash, block.timestamp);
    }

    function getDocument(bytes32 documentHash)
        external
        view
        returns (
            string memory issuer,
            uint256 issuedAt,
            uint256 expiry,
            bool active,
            bool exists
        )
    {
        Document memory d = documents[documentHash];
        return (d.issuer, d.issuedAt, d.expiry, d.active, d.exists);
    }
}
