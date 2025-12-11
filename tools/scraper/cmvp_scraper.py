#!/usr/bin/env python3
"""
CMVP Certificate Scraper

Scrapes certificate data from NIST CMVP pages.
Respects rate limits and caches results.

Note: Until NIST provides a public API (expected late 2025),
this scraper is the primary method for obtaining certificate data.
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import aiohttp
    from bs4 import BeautifulSoup
except ImportError:
    print("Required packages not installed. Run: pip install aiohttp beautifulsoup4 lxml")
    sys.exit(1)

from rate_limiter import RateLimiter


class CMVPScraper:
    """Scrapes CMVP certificate information from NIST website."""

    BASE_URL = "https://csrc.nist.gov/projects/cryptographic-module-validation-program/certificate"

    def __init__(
        self,
        cache_dir: Path,
        requests_per_minute: int = 30
    ):
        self.cache_dir = cache_dir
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.session: Optional[aiohttp.ClientSession] = None
        self.stats = {
            'fetched': 0,
            'cached': 0,
            'errors': 0,
            'not_found': 0
        }

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                'User-Agent': 'FedRAMP-CryptoModule-Validator/1.0 (github.com/fedramp/crypto-modules)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            },
            timeout=aiohttp.ClientTimeout(total=30)
        )
        return self

    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()

    async def fetch_certificate(self, cert_number: int) -> Optional[dict]:
        """Fetch and parse a single certificate page."""
        await self.rate_limiter.acquire()

        url = f"{self.BASE_URL}/{cert_number}"

        try:
            async with self.session.get(url) as response:
                if response.status == 404:
                    self.stats['not_found'] += 1
                    return None
                response.raise_for_status()
                html = await response.text()
                self.stats['fetched'] += 1
        except aiohttp.ClientError as e:
            print(f"  Error fetching cert {cert_number}: {e}", file=sys.stderr)
            self.stats['errors'] += 1
            return None

        return self._parse_certificate_page(html, cert_number)

    def _parse_certificate_page(self, html: str, cert_number: int) -> dict:
        """Parse HTML content into structured data."""
        soup = BeautifulSoup(html, 'lxml')

        cert_data = {
            'certificateNumber': cert_number,
            'lastScraped': datetime.utcnow().isoformat() + 'Z'
        }

        # Extract module name from the page header
        header = soup.find('h1')
        if header:
            cert_data['moduleName'] = self._clean_text(header.text)

        # Parse the certificate details table
        # NIST uses various table structures, so we check multiple patterns
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2:
                    key = self._clean_text(cells[0].text).lower()
                    value = self._clean_text(cells[1].text)
                    self._extract_field(cert_data, key, value)

        # Also check for definition lists (dl/dt/dd)
        for dl in soup.find_all('dl'):
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            for dt, dd in zip(dts, dds):
                key = self._clean_text(dt.text).lower()
                value = self._clean_text(dd.text)
                self._extract_field(cert_data, key, value)

        # Extract algorithms from dedicated sections
        algorithms = self._extract_algorithms(soup)
        if algorithms:
            cert_data['algorithms'] = algorithms

        return cert_data

    def _extract_field(self, cert_data: dict, key: str, value: str):
        """Extract a field based on the key."""
        if not value or value.lower() == 'n/a':
            return

        if 'vendor' in key and 'vendor' not in cert_data:
            cert_data['vendor'] = {'name': value}
        elif 'status' in key and 'status' not in cert_data:
            # Normalize status values
            if 'active' in value.lower():
                cert_data['status'] = 'Active'
            elif 'historical' in value.lower():
                cert_data['status'] = 'Historical'
            elif 'revoked' in value.lower():
                cert_data['status'] = 'Revoked'
            else:
                cert_data['status'] = value
        elif 'module type' in key and 'moduleType' not in cert_data:
            cert_data['moduleType'] = value
        elif 'embodiment' in key and 'embodiment' not in cert_data:
            cert_data['embodiment'] = value
        elif 'overall level' in key or 'security level' in key:
            match = re.search(r'\d+', value)
            if match:
                cert_data['securityLevel'] = int(match.group())
        elif 'validation date' in key or 'validated' in key:
            date = self._parse_date(value)
            if date:
                cert_data['validationDate'] = date
        elif 'sunset' in key or 'expir' in key:
            date = self._parse_date(value)
            if date:
                cert_data['sunsetDate'] = date
        elif 'standard' in key and 'standard' not in cert_data:
            if '140-3' in value:
                cert_data['standard'] = 'FIPS 140-3'
            elif '140-2' in value:
                cert_data['standard'] = 'FIPS 140-2'
            elif '140-1' in value:
                cert_data['standard'] = 'FIPS 140-1'
        elif 'software' in key and 'version' in key:
            if 'versions' not in cert_data:
                cert_data['versions'] = {}
            cert_data['versions']['software'] = value
        elif 'hardware' in key and 'version' in key:
            if 'versions' not in cert_data:
                cert_data['versions'] = {}
            cert_data['versions']['hardware'] = value
        elif 'firmware' in key and 'version' in key:
            if 'versions' not in cert_data:
                cert_data['versions'] = {}
            cert_data['versions']['firmware'] = value

    def _extract_algorithms(self, soup: BeautifulSoup) -> list:
        """Extract algorithm list from the page."""
        algorithms = set()

        # Look for algorithm sections
        for text in soup.stripped_strings:
            text_lower = text.lower()
            if any(alg in text_lower for alg in ['aes', 'rsa', 'sha', 'ecdsa', 'hmac', 'drbg']):
                # Extract known algorithm names
                if 'aes' in text_lower:
                    algorithms.add('AES')
                if 'rsa' in text_lower:
                    algorithms.add('RSA')
                if 'sha-2' in text_lower or 'sha2' in text_lower or 'sha-256' in text_lower or 'sha-512' in text_lower:
                    algorithms.add('SHA-2')
                if 'sha-3' in text_lower or 'sha3' in text_lower:
                    algorithms.add('SHA-3')
                if 'sha-1' in text_lower or 'sha1' in text_lower:
                    algorithms.add('SHA-1')
                if 'ecdsa' in text_lower:
                    algorithms.add('ECDSA')
                if 'ecdh' in text_lower:
                    algorithms.add('ECDH')
                if 'hmac' in text_lower:
                    algorithms.add('HMAC')
                if 'drbg' in text_lower:
                    algorithms.add('DRBG')
                if 'kdf' in text_lower:
                    algorithms.add('KDF')
                if 'triple-des' in text_lower or '3des' in text_lower or 'tdes' in text_lower:
                    algorithms.add('Triple-DES')

        return sorted(algorithms) if algorithms else []

    @staticmethod
    def _clean_text(text: str) -> str:
        """Clean extracted text."""
        return re.sub(r'\s+', ' ', text).strip()

    @staticmethod
    def _parse_date(date_str: str) -> Optional[str]:
        """Parse date string to ISO format."""
        formats = [
            '%m/%d/%Y',
            '%Y-%m-%d',
            '%B %d, %Y',
            '%b %d, %Y',
            '%d %B %Y',
            '%d %b %Y',
        ]
        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None

    async def update_range(
        self,
        start: int,
        end: int,
        output_file: Path,
        batch_size: int = 50
    ) -> dict:
        """Scrape a range of certificates."""
        certificates = {}

        # Load existing cache if present
        if output_file.exists():
            try:
                with open(output_file) as f:
                    certificates = json.load(f)
                print(f"  Loaded {len(certificates)} existing certificates from cache")
            except json.JSONDecodeError:
                certificates = {}

        # Process in batches to save progress periodically
        for batch_start in range(start, end + 1, batch_size):
            batch_end = min(batch_start + batch_size - 1, end)
            print(f"  Fetching certificates {batch_start}-{batch_end}...")

            tasks = [
                self.fetch_certificate(n)
                for n in range(batch_start, batch_end + 1)
                if str(n) not in certificates  # Skip already cached
            ]

            if not tasks:
                self.stats['cached'] += batch_end - batch_start + 1
                continue

            results = await asyncio.gather(*tasks)

            for result in results:
                if result:
                    certificates[str(result['certificateNumber'])] = result

            # Save progress after each batch
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(certificates, f, indent=2)

        return certificates

    def print_stats(self):
        """Print scraping statistics."""
        print(f"\nScraping Statistics:")
        print(f"  Fetched: {self.stats['fetched']}")
        print(f"  Cached: {self.stats['cached']}")
        print(f"  Not Found: {self.stats['not_found']}")
        print(f"  Errors: {self.stats['errors']}")


async def main():
    parser = argparse.ArgumentParser(
        description='Scrape CMVP certificate data from NIST'
    )
    parser.add_argument(
        '--start',
        type=int,
        default=4000,
        help='Starting certificate number (default: 4000)'
    )
    parser.add_argument(
        '--end',
        type=int,
        default=5999,
        help='Ending certificate number (default: 5999)'
    )
    parser.add_argument(
        '--output',
        '-o',
        type=Path,
        default=Path('cmvp-cache'),
        help='Output directory for cache files'
    )
    parser.add_argument(
        '--rate-limit',
        type=int,
        default=30,
        help='Requests per minute (default: 30)'
    )
    parser.add_argument(
        '--single',
        type=int,
        help='Fetch a single certificate number'
    )

    args = parser.parse_args()

    async with CMVPScraper(args.output, args.rate_limit) as scraper:
        if args.single:
            print(f"Fetching certificate #{args.single}...")
            result = await scraper.fetch_certificate(args.single)
            if result:
                print(json.dumps(result, indent=2))
            else:
                print("Certificate not found")
        else:
            # Determine output file based on range
            range_start = (args.start // 1000) * 1000
            range_end = ((args.end // 1000) + 1) * 1000 - 1
            output_file = args.output / 'certificates' / f'{range_start:04d}-{range_end:04d}.json'

            print(f"Scraping certificates {args.start}-{args.end}...")
            print(f"Output file: {output_file}")
            print(f"Rate limit: {args.rate_limit} requests/minute")
            print()

            await scraper.update_range(
                args.start,
                args.end,
                output_file
            )

            scraper.print_stats()

            # Update metadata
            await update_metadata(args.output)


async def update_metadata(cache_dir: Path):
    """Update the cache metadata file."""
    metadata = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'source': 'https://csrc.nist.gov/projects/cryptographic-module-validation-program',
        'rangesCached': [],
        'statusCounts': {
            'Active': 0,
            'Historical': 0,
            'Revoked': 0
        },
        'totalCertificates': 0
    }

    cert_dir = cache_dir / 'certificates'
    if cert_dir.exists():
        for cache_file in sorted(cert_dir.glob('*.json')):
            try:
                with open(cache_file) as f:
                    data = json.load(f)

                # Extract range from filename
                match = re.match(r'(\d+)-(\d+)\.json', cache_file.name)
                if match:
                    metadata['rangesCached'].append({
                        'start': int(match.group(1)),
                        'end': int(match.group(2)),
                        'file': f'certificates/{cache_file.name}'
                    })

                # Count certificates and statuses
                for cert in data.values():
                    metadata['totalCertificates'] += 1
                    status = cert.get('status', 'Unknown')
                    if status in metadata['statusCounts']:
                        metadata['statusCounts'][status] += 1

            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not read {cache_file}: {e}", file=sys.stderr)

    # Write metadata
    metadata_file = cache_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f, indent=2)

    print(f"\nMetadata updated: {metadata_file}")
    print(f"  Total certificates: {metadata['totalCertificates']}")
    print(f"  Status counts: {metadata['statusCounts']}")


if __name__ == '__main__':
    asyncio.run(main())
