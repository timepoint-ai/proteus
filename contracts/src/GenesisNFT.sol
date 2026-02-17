// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/utils/Base64.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title GenesisNFT
 * @dev Part of the Proteus protocol (formerly Clockchain).
 * Fixed supply of 100 Genesis NFTs providing founder rewards.
 * Features:
 * - Immutable 100 NFT cap
 * - On-chain SVG art generation
 * - One-time minting with automatic finalization
 * - No admin functions after deployment
 * - 0.002% platform volume reward per NFT
 */
contract GenesisNFT is ERC721Enumerable {
    using Strings for uint256;
    
    // Constants
    uint256 public constant MAX_SUPPLY = 100;
    uint256 public constant MINTING_WINDOW = 24 hours;
    
    // State variables
    uint256 public mintingDeadline;
    bool public mintingFinalized;
    uint256 private _tokenIdCounter;
    
    // Events
    event MintingFinalized(uint256 totalMinted);
    event GenesisNFTMinted(address indexed to, uint256 tokenId);
    
    /**
     * @dev Constructor sets up the NFT with a 24-hour minting window
     */
    // Legacy: ERC721 name is immutable on-chain. 60 NFTs already minted with "Clockchain Genesis" branding.
    constructor() ERC721("Clockchain Genesis", "GENESIS") {
        mintingDeadline = block.timestamp + MINTING_WINDOW;
        _tokenIdCounter = 1; // Start from token ID 1
    }
    
    /**
     * @dev Mint Genesis NFTs - can only be called within the minting window
     * @param to Address to mint NFTs to
     * @param quantity Number of NFTs to mint
     */
    function mint(address to, uint256 quantity) external {
        require(!mintingFinalized, "Minting has been finalized");
        require(block.timestamp <= mintingDeadline, "Minting window has expired");
        require(_tokenIdCounter + quantity - 1 <= MAX_SUPPLY, "Would exceed max supply");
        require(to != address(0), "Cannot mint to zero address");
        require(quantity > 0 && quantity <= 10, "Invalid quantity");
        
        for (uint256 i = 0; i < quantity; i++) {
            uint256 tokenId = _tokenIdCounter++;
            _safeMint(to, tokenId);
            emit GenesisNFTMinted(to, tokenId);
        }
        
        // Auto-finalize if we hit max supply
        if (_tokenIdCounter > MAX_SUPPLY) {
            _finalizeMinting();
        }
    }
    
    /**
     * @dev Finalize minting - can be called by anyone after deadline
     * Prevents any future minting
     */
    function finalizeMinting() external {
        require(!mintingFinalized, "Already finalized");
        require(
            block.timestamp > mintingDeadline || _tokenIdCounter > MAX_SUPPLY,
            "Cannot finalize yet"
        );
        
        _finalizeMinting();
    }
    
    /**
     * @dev Internal function to finalize minting
     */
    function _finalizeMinting() private {
        mintingFinalized = true;
        emit MintingFinalized(_tokenIdCounter - 1);
    }
    
    /**
     * @dev Generate on-chain SVG art for each NFT
     * Creates unique visual based on token ID
     */
    function generateSVG(uint256 tokenId) public pure returns (string memory) {
        require(tokenId > 0 && tokenId <= MAX_SUPPLY, "Invalid token ID");
        
        // Generate unique colors based on token ID
        string memory primaryColor = generateColor(tokenId);
        string memory secondaryColor = generateColor(tokenId + 100);
        string memory accentColor = generateColor(tokenId + 200);
        
        // Create SVG with unique pattern for each NFT
        string memory svg = string(abi.encodePacked(
            '<svg xmlns="http://www.w3.org/2000/svg" width="500" height="500" viewBox="0 0 500 500">',
            '<defs>',
            '<linearGradient id="grad', tokenId.toString(), '" x1="0%" y1="0%" x2="100%" y2="100%">',
            '<stop offset="0%" style="stop-color:', primaryColor, ';stop-opacity:1" />',
            '<stop offset="50%" style="stop-color:', secondaryColor, ';stop-opacity:1" />',
            '<stop offset="100%" style="stop-color:', accentColor, ';stop-opacity:1" />',
            '</linearGradient>',
            '<filter id="glow">',
            '<feGaussianBlur stdDeviation="4" result="coloredBlur"/>',
            '<feMerge>',
            '<feMergeNode in="coloredBlur"/>',
            '<feMergeNode in="SourceGraphic"/>',
            '</feMerge>',
            '</filter>',
            '</defs>'
        ));
        
        svg = string(abi.encodePacked(
            svg,
            '<rect width="500" height="500" fill="url(#grad', tokenId.toString(), ')"/>',
            '<g filter="url(#glow)">',
            generateGeometricPattern(tokenId),
            '</g>',
            '<text x="250" y="450" font-family="monospace" font-size="24" fill="white" text-anchor="middle" font-weight="bold">',
            'GENESIS #', tokenId.toString(),
            '</text>',
            '<text x="250" y="475" font-family="monospace" font-size="14" fill="white" text-anchor="middle" opacity="0.8">',
            // Legacy: on-chain SVG text for all minted Genesis NFTs. Cannot be changed retroactively.
            'CLOCKCHAIN FOUNDER',
            '</text>',
            '</svg>'
        ));
        
        return svg;
    }
    
    /**
     * @dev Generate unique geometric pattern for each NFT
     */
    function generateGeometricPattern(uint256 tokenId) private pure returns (string memory) {
        string memory pattern = '';
        uint256 seed = tokenId;
        
        // Create concentric hexagons with rotating angles
        for (uint256 i = 0; i < 5; i++) {
            uint256 size = 180 - (i * 30);
            uint256 rotation = (seed * 13 + i * 60) % 360;
            uint256 opacity = 100 - (i * 15);
            
            pattern = string(abi.encodePacked(
                pattern,
                '<polygon points="',
                generateHexagonPoints(250, 250, size),
                '" fill="none" stroke="white" stroke-width="2" opacity="0.', 
                (opacity).toString(),
                '" transform="rotate(', rotation.toString(), ' 250 250)"/>'
            ));
            
            seed = (seed * 7) % 100;
        }
        
        // Add central clock-themed element
        pattern = string(abi.encodePacked(
            pattern,
            '<circle cx="250" cy="250" r="50" fill="none" stroke="white" stroke-width="3" opacity="0.9"/>',
            '<line x1="250" y1="250" x2="250" y2="210" stroke="white" stroke-width="3" stroke-linecap="round" transform="rotate(', (tokenId * 30).toString(), ' 250 250)"/>',
            '<line x1="250" y1="250" x2="280" y2="250" stroke="white" stroke-width="2" stroke-linecap="round" transform="rotate(', (tokenId * 45).toString(), ' 250 250)"/>',
            '<circle cx="250" cy="250" r="5" fill="white"/>'
        ));
        
        return pattern;
    }
    
    /**
     * @dev Generate hexagon points for SVG polygon
     */
    function generateHexagonPoints(uint256 cx, uint256 cy, uint256 size) private pure returns (string memory) {
        string memory points = '';
        
        for (uint256 i = 0; i < 6; i++) {
            uint256 angle = i * 60;
            int256 xOffset = (int256(size) * cos(angle)) / 100;
            int256 yOffset = (int256(size) * sin(angle)) / 100;
            uint256 x = xOffset >= 0 ? cx + uint256(xOffset) : cx - uint256(-xOffset);
            uint256 y = yOffset >= 0 ? cy + uint256(yOffset) : cy - uint256(-yOffset);
            
            if (i > 0) points = string(abi.encodePacked(points, ' '));
            points = string(abi.encodePacked(points, x.toString(), ',', y.toString()));
        }
        
        return points;
    }
    
    /**
     * @dev Simple cosine approximation for SVG generation
     */
    function cos(uint256 angle) private pure returns (int256) {
        // Simple approximation for common angles
        if (angle == 0) return 100;
        if (angle == 60) return 50;
        if (angle == 120) return -50;
        if (angle == 180) return -100;
        if (angle == 240) return -50;
        if (angle == 300) return 50;
        return 0;
    }
    
    /**
     * @dev Simple sine approximation for SVG generation
     */
    function sin(uint256 angle) private pure returns (int256) {
        // Simple approximation for common angles
        if (angle == 0) return 0;
        if (angle == 60) return 87;
        if (angle == 120) return 87;
        if (angle == 180) return 0;
        if (angle == 240) return -87;
        if (angle == 300) return -87;
        return 0;
    }
    
    /**
     * @dev Generate color from seed value
     */
    function generateColor(uint256 seed) private pure returns (string memory) {
        uint256 hash = uint256(keccak256(abi.encodePacked(seed)));
        
        // Extract RGB values
        uint256 r = (hash % 128) + 100; // Range: 100-227 (avoid too dark)
        uint256 g = ((hash / 256) % 128) + 100;
        uint256 b = ((hash / 65536) % 128) + 100;
        
        return string(abi.encodePacked(
            "rgb(",
            r.toString(), ",",
            g.toString(), ",",
            b.toString(), ")"
        ));
    }
    
    /**
     * @dev Returns the token URI with on-chain metadata
     */
    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        require(tokenId > 0 && tokenId <= _tokenIdCounter - 1, "Token does not exist");
        
        string memory svg = generateSVG(tokenId);
        string memory json = Base64.encode(
            bytes(
                string(abi.encodePacked(
                    '{"name": "Clockchain Genesis #', tokenId.toString(), '",',
                    '"description": "One of 100 Genesis NFTs providing founder rewards for the Clockchain prediction platform. Each NFT receives 0.002% of platform volume.",',
                    '"image": "data:image/svg+xml;base64,', Base64.encode(bytes(svg)), '",',
                    '"attributes": [',
                    '{"trait_type": "Collection", "value": "Genesis"},',
                    '{"trait_type": "Reward Percentage", "value": "0.002%"},',
                    '{"trait_type": "Total Supply", "value": "100"},',
                    '{"trait_type": "Number", "value": ', tokenId.toString(), '}',
                    ']}'
                ))
            )
        );
        
        return string(abi.encodePacked("data:application/json;base64,", json));
    }
    
    /**
     * @dev Check if minting is still active
     */
    function isMintingActive() external view returns (bool) {
        return !mintingFinalized && block.timestamp <= mintingDeadline;
    }
    
    /**
     * @dev Get remaining mintable supply
     */
    function remainingSupply() external view returns (uint256) {
        if (mintingFinalized) return 0;
        return MAX_SUPPLY - (_tokenIdCounter - 1);
    }
    
    /**
     * @dev Get total minted so far
     */
    function totalMinted() external view returns (uint256) {
        return _tokenIdCounter - 1;
    }
}