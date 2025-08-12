const { expect } = require("chai");
const { ethers } = require("hardhat");
const { time } = require("@nomicfoundation/hardhat-network-helpers");

describe("GenesisNFT", function () {
    let genesisNFT;
    let owner, addr1, addr2, addr3;
    const MINTING_WINDOW = 24 * 60 * 60; // 24 hours in seconds
    const MAX_SUPPLY = 100;

    beforeEach(async function () {
        [owner, addr1, addr2, addr3] = await ethers.getSigners();
        
        const GenesisNFT = await ethers.getContractFactory("GenesisNFT");
        genesisNFT = await GenesisNFT.deploy();
        await genesisNFT.waitForDeployment();
    });

    describe("Deployment", function () {
        it("Should set the correct name and symbol", async function () {
            expect(await genesisNFT.name()).to.equal("Clockchain Genesis");
            expect(await genesisNFT.symbol()).to.equal("GENESIS");
        });

        it("Should set the correct max supply", async function () {
            expect(await genesisNFT.MAX_SUPPLY()).to.equal(MAX_SUPPLY);
        });

        it("Should set the minting deadline correctly", async function () {
            const deadline = await genesisNFT.mintingDeadline();
            const currentTime = await time.latest();
            expect(deadline).to.be.closeTo(currentTime + MINTING_WINDOW, 5);
        });

        it("Should not be finalized initially", async function () {
            expect(await genesisNFT.mintingFinalized()).to.equal(false);
        });
    });

    describe("Minting", function () {
        it("Should mint NFTs within the minting window", async function () {
            await genesisNFT.mint(addr1.address, 5);
            expect(await genesisNFT.balanceOf(addr1.address)).to.equal(5);
            expect(await genesisNFT.totalSupply()).to.equal(5);
        });

        it("Should emit GenesisNFTMinted event", async function () {
            await expect(genesisNFT.mint(addr1.address, 1))
                .to.emit(genesisNFT, "GenesisNFTMinted")
                .withArgs(addr1.address, 1);
        });

        it("Should not allow minting more than 10 at once", async function () {
            await expect(genesisNFT.mint(addr1.address, 11))
                .to.be.revertedWith("Invalid quantity");
        });

        it("Should not allow minting 0 NFTs", async function () {
            await expect(genesisNFT.mint(addr1.address, 0))
                .to.be.revertedWith("Invalid quantity");
        });

        it("Should not allow minting to zero address", async function () {
            await expect(genesisNFT.mint(ethers.ZeroAddress, 1))
                .to.be.revertedWith("Cannot mint to zero address");
        });

        it("Should not exceed max supply", async function () {
            // Mint 95 NFTs first
            for (let i = 0; i < 10; i++) {
                if (i < 9) {
                    await genesisNFT.mint(addr1.address, 10);
                } else {
                    await genesisNFT.mint(addr1.address, 5);
                }
            }
            
            // Try to mint 6 more (would exceed 100)
            await expect(genesisNFT.mint(addr2.address, 6))
                .to.be.revertedWith("Would exceed max supply");
        });

        it("Should auto-finalize when reaching max supply", async function () {
            // Mint exactly 100 NFTs
            for (let i = 0; i < 10; i++) {
                await genesisNFT.mint(addr1.address, 10);
            }
            
            expect(await genesisNFT.mintingFinalized()).to.equal(true);
            expect(await genesisNFT.totalSupply()).to.equal(100);
        });

        it("Should not allow minting after minting window expires", async function () {
            // Fast forward past the minting window
            await time.increase(MINTING_WINDOW + 1);
            
            await expect(genesisNFT.mint(addr1.address, 1))
                .to.be.revertedWith("Minting window has expired");
        });

        it("Should not allow minting after finalization", async function () {
            // Mint to max supply to trigger auto-finalization
            for (let i = 0; i < 10; i++) {
                await genesisNFT.mint(addr1.address, 10);
            }
            
            await expect(genesisNFT.mint(addr2.address, 1))
                .to.be.revertedWith("Minting has been finalized");
        });
    });

    describe("Finalization", function () {
        it("Should allow finalization after deadline", async function () {
            await time.increase(MINTING_WINDOW + 1);
            
            await expect(genesisNFT.finalizeMinting())
                .to.emit(genesisNFT, "MintingFinalized");
                
            expect(await genesisNFT.mintingFinalized()).to.equal(true);
        });

        it("Should not allow finalization before deadline", async function () {
            await expect(genesisNFT.finalizeMinting())
                .to.be.revertedWith("Cannot finalize yet");
        });

        it("Should not allow double finalization", async function () {
            await time.increase(MINTING_WINDOW + 1);
            await genesisNFT.finalizeMinting();
            
            await expect(genesisNFT.finalizeMinting())
                .to.be.revertedWith("Already finalized");
        });

        it("Should emit MintingFinalized event with correct total", async function () {
            await genesisNFT.mint(addr1.address, 5);
            await time.increase(MINTING_WINDOW + 1);
            
            await expect(genesisNFT.finalizeMinting())
                .to.emit(genesisNFT, "MintingFinalized")
                .withArgs(5);
        });
    });

    describe("Token URI and Metadata", function () {
        beforeEach(async function () {
            await genesisNFT.mint(addr1.address, 3);
        });

        it("Should generate valid SVG for each token", async function () {
            const svg = await genesisNFT.generateSVG(1);
            expect(svg).to.include('<svg');
            expect(svg).to.include('GENESIS #1');
            expect(svg).to.include('CLOCKCHAIN FOUNDER');
        });

        it("Should generate unique SVGs for different tokens", async function () {
            const svg1 = await genesisNFT.generateSVG(1);
            const svg2 = await genesisNFT.generateSVG(2);
            expect(svg1).to.not.equal(svg2);
        });

        it("Should return valid token URI with on-chain metadata", async function () {
            const tokenURI = await genesisNFT.tokenURI(1);
            expect(tokenURI).to.include('data:application/json;base64,');
            
            // Decode and verify JSON structure
            const base64Data = tokenURI.replace('data:application/json;base64,', '');
            const jsonString = Buffer.from(base64Data, 'base64').toString('utf8');
            const metadata = JSON.parse(jsonString);
            
            expect(metadata.name).to.equal('Clockchain Genesis #1');
            expect(metadata.description).to.include('0.002% of platform volume');
            expect(metadata.attributes).to.have.lengthOf(4);
        });

        it("Should revert for non-existent token", async function () {
            await expect(genesisNFT.tokenURI(999))
                .to.be.revertedWith("Token does not exist");
        });

        it("Should revert generateSVG for invalid token ID", async function () {
            await expect(genesisNFT.generateSVG(0))
                .to.be.revertedWith("Invalid token ID");
            await expect(genesisNFT.generateSVG(101))
                .to.be.revertedWith("Invalid token ID");
        });
    });

    describe("View Functions", function () {
        it("Should correctly report minting status", async function () {
            expect(await genesisNFT.isMintingActive()).to.equal(true);
            
            await time.increase(MINTING_WINDOW + 1);
            expect(await genesisNFT.isMintingActive()).to.equal(false);
        });

        it("Should correctly report remaining supply", async function () {
            expect(await genesisNFT.remainingSupply()).to.equal(100);
            
            await genesisNFT.mint(addr1.address, 10);
            expect(await genesisNFT.remainingSupply()).to.equal(90);
            
            // After finalization
            await time.increase(MINTING_WINDOW + 1);
            await genesisNFT.finalizeMinting();
            expect(await genesisNFT.remainingSupply()).to.equal(0);
        });

        it("Should correctly report total minted", async function () {
            expect(await genesisNFT.totalMinted()).to.equal(0);
            
            await genesisNFT.mint(addr1.address, 5);
            expect(await genesisNFT.totalMinted()).to.equal(5);
            
            await genesisNFT.mint(addr2.address, 3);
            expect(await genesisNFT.totalMinted()).to.equal(8);
        });
    });

    describe("ERC721 Functionality", function () {
        beforeEach(async function () {
            await genesisNFT.mint(addr1.address, 3);
            await genesisNFT.mint(addr2.address, 2);
        });

        it("Should support transfers", async function () {
            await genesisNFT.connect(addr1).transferFrom(addr1.address, addr3.address, 1);
            expect(await genesisNFT.ownerOf(1)).to.equal(addr3.address);
            expect(await genesisNFT.balanceOf(addr1.address)).to.equal(2);
            expect(await genesisNFT.balanceOf(addr3.address)).to.equal(1);
        });

        it("Should support approvals", async function () {
            await genesisNFT.connect(addr1).approve(addr2.address, 1);
            expect(await genesisNFT.getApproved(1)).to.equal(addr2.address);
            
            await genesisNFT.connect(addr2).transferFrom(addr1.address, addr3.address, 1);
            expect(await genesisNFT.ownerOf(1)).to.equal(addr3.address);
        });

        it("Should enumerate tokens correctly", async function () {
            expect(await genesisNFT.tokenOfOwnerByIndex(addr1.address, 0)).to.equal(1);
            expect(await genesisNFT.tokenOfOwnerByIndex(addr1.address, 1)).to.equal(2);
            expect(await genesisNFT.tokenOfOwnerByIndex(addr1.address, 2)).to.equal(3);
            
            expect(await genesisNFT.tokenOfOwnerByIndex(addr2.address, 0)).to.equal(4);
            expect(await genesisNFT.tokenOfOwnerByIndex(addr2.address, 1)).to.equal(5);
        });
    });

    describe("Security", function () {
        it("Should not have any owner-only functions", async function () {
            // Verify the contract has no owner-related functions
            // This is a conceptual test - in reality, we'd check the ABI
            const contractABI = genesisNFT.interface.fragments;
            const ownerFunctions = contractABI.filter(f => 
                f.name && (f.name.includes('owner') || f.name.includes('Owner'))
            );
            expect(ownerFunctions.length).to.equal(0);
        });

        it("Should be truly immutable after finalization", async function () {
            // Mint some NFTs and finalize
            await genesisNFT.mint(addr1.address, 10);
            await time.increase(MINTING_WINDOW + 1);
            await genesisNFT.finalizeMinting();
            
            // Try various operations that should all fail
            await expect(genesisNFT.mint(addr2.address, 1))
                .to.be.revertedWith("Minting has been finalized");
            
            // The total supply should remain fixed
            expect(await genesisNFT.totalSupply()).to.equal(10);
        });
    });
});