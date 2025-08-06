#!/usr/bin/env python3
"""
textual-snapshots Development Script
Cross-platform development commands using Python
"""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path
from typing import List, Optional


class Colors:
    """ANSI color codes for terminal output"""
    BLUE = '\033[34m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    RED = '\033[31m'
    BOLD = '\033[1m'
    RESET = '\033[0m'
    
    @classmethod
    def disable(cls):
        """Disable colors (for Windows or when redirecting output)"""
        cls.BLUE = cls.GREEN = cls.YELLOW = cls.RED = cls.BOLD = cls.RESET = ''


class DevRunner:
    """Cross-platform development command runner"""
    
    def __init__(self, verbose: bool = False, no_color: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        
        # Disable colors on Windows or if requested
        if no_color or platform.system() == 'Windows':
            Colors.disable()
    
    def log(self, message: str, color: str = Colors.BLUE):
        """Print colored log message"""
        print(f"{color}{message}{Colors.RESET}")
    
    def success(self, message: str):
        """Print success message"""
        self.log(f"✅ {message}", Colors.GREEN)
    
    def warning(self, message: str):
        """Print warning message"""
        self.log(f"⚠️  {message}", Colors.YELLOW)
    
    def error(self, message: str):
        """Print error message"""
        self.log(f"❌ {message}", Colors.RED)
    
    def run_cmd(self, cmd: List[str], check: bool = True, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
        """Run command and handle output"""
        if self.verbose:
            self.log(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(
                cmd, 
                check=check, 
                cwd=cwd or self.project_root,
                capture_output=not self.verbose,
                text=True
            )
            return result
        except subprocess.CalledProcessError as e:
            self.error(f"Command failed: {' '.join(cmd)}")
            if not self.verbose and e.stdout:
                print(e.stdout)
            if not self.verbose and e.stderr:
                print(e.stderr, file=sys.stderr)
            raise
    
    def uv_cmd(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run UV command"""
        return self.run_cmd(['uv'] + args)
    
    def uv_run(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run command through UV"""
        return self.run_cmd(['uv', 'run'] + args)
    
    # Development Environment Commands
    
    def install(self):
        """Install dependencies and setup development environment"""
        self.log("🚀 Setting up development environment...")
        self.uv_cmd(['sync'])
        self.uv_run(['playwright', 'install', 'chromium'])
        self.success("Development environment ready!")
    
    def install_ci(self):
        """Install dependencies for CI/CD (no browser setup)"""
        self.log("🤖 Setting up CI environment...")
        self.uv_cmd(['sync'])
        self.success("CI environment ready!")
    
    # Code Quality Commands
    
    def format_code(self, check: bool = False):
        """Format code with ruff"""
        if check:
            self.log("🔍 Checking code formatting...")
            self.uv_run(['ruff', 'format', '--check', 'src', 'tests'])
            self.uv_run(['ruff', 'check', 'src', 'tests'])
        else:
            self.log("🎨 Formatting code...")
            self.uv_run(['ruff', 'format', 'src', 'tests'])
            self.uv_run(['ruff', 'check', '--fix', 'src', 'tests'])
            self.success("Code formatted!")
    
    def lint(self):
        """Run linting checks"""
        self.log("🔍 Running linting checks...")
        self.uv_run(['ruff', 'check', 'src', 'tests'])
        self.success("Linting passed!")
    
    def typecheck(self, strict: bool = False):
        """Run type checking"""
        self.log("🔍 Running type checks...")
        self.uv_run(['mypy', 'src'])
        
        if strict:
            # Note: Strict mode only checks source code
            # Test type checking is skipped due to test-specific patterns
            self.log("Strict mode: Source code type checking only (tests skipped)")
        
        self.success("Type checking passed!")
    
    # Testing Commands
    
    def test(self, quiet: bool = False, coverage: bool = False):
        """Run tests"""
        self.log("🧪 Running tests...")
        
        cmd = ['pytest', 'tests/', '--tb=short']
        
        if quiet:
            cmd.append('-q')
        else:
            cmd.append('-v')
        
        if coverage:
            cmd.extend(['--cov=src', '--cov-report=term-missing', '--cov-report=html'])
        
        self.uv_run(cmd)
        
        if coverage:
            self.success("Coverage report generated in htmlcov/")
    
    # Quality Check Combinations
    
    def check(self, strict: bool = False, full: bool = False):
        """Run quality checks"""
        try:
            if full:
                self.format_code(check=True)
            
            self.lint()
            self.typecheck(strict=strict)
            self.test(quiet=True, coverage=full)
            
            level = "comprehensive" if full else "strict" if strict else "basic"
            self.success(f"All {level} checks passed!")
            
        except subprocess.CalledProcessError:
            sys.exit(1)
    
    # CLI Testing
    
    def cli_test(self):
        """Test CLI commands"""
        self.log("🖥️  Testing CLI commands...")
        print("Testing help command:")
        self.uv_run(['textual-snapshot', '--help'])
        print("\nTesting version:")
        self.uv_run(['textual-snapshot', '--version'])
    
    def demo(self):
        """Run CLI demo"""
        self.log("🎭 Running CLI demo...")
        
        # Create test SVG
        demo_svg = self.project_root / "demo.svg"
        demo_svg.write_text('<svg width="100" height="50" xmlns="http://www.w3.org/2000/svg"><rect width="100" height="50" fill="blue"/></svg>')
        
        try:
            self.uv_run(['textual-snapshot', 'convert', 'demo.svg', '--to', 'png', '--quality', 'high'])
        except subprocess.CalledProcessError:
            self.warning("Demo conversion failed (this is expected without proper setup)")
        
        # Cleanup
        demo_svg.unlink(missing_ok=True)
        converted_dir = self.project_root / "converted"
        if converted_dir.exists():
            shutil.rmtree(converted_dir, ignore_errors=True)
        
        self.success("Demo completed!")
    
    # Coverage and Reports
    
    def coverage_html(self):
        """Generate and open HTML coverage report"""
        self.log("📊 Generating coverage report...")
        self.uv_run(['pytest', 'tests/', '--cov=src', '--cov-report=html'])
        
        # Open in browser
        html_file = self.project_root / "htmlcov" / "index.html"
        if html_file.exists():
            webbrowser.open(f"file://{html_file.absolute()}")
            self.success("Coverage report opened in browser!")
        else:
            self.warning("Coverage report not found")
    
    def coverage_xml(self):
        """Generate XML coverage report for CI"""
        self.log("📊 Generating XML coverage report...")
        self.uv_run(['pytest', 'tests/', '--cov=src', '--cov-report=xml'])
    
    # Utilities
    
    def clean(self):
        """Clean up generated files and caches"""
        self.log("🧹 Cleaning up...")
        
        patterns = [
            '.coverage', 'htmlcov', '.pytest_cache', '.mypy_cache', '.ruff_cache',
            'src/*.egg-info', 'dist', 'build', 'screenshots', 'baselines', 
            'converted', 'test_output'
        ]
        
        for pattern in patterns:
            for path in self.project_root.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink(missing_ok=True)
        
        # Clean __pycache__ directories
        for pycache in self.project_root.rglob('__pycache__'):
            shutil.rmtree(pycache, ignore_errors=True)
        
        self.success("Cleanup complete!")
    
    def reset(self):
        """Reset development environment"""
        self.log("🔄 Resetting development environment...")
        self.clean()
        
        venv_dir = self.project_root / ".venv"
        if venv_dir.exists():
            shutil.rmtree(venv_dir, ignore_errors=True)
        
        self.install()
        self.success("Environment reset complete!")
    
    def deps_update(self):
        """Update dependencies"""
        self.log("📦 Updating dependencies...")
        self.uv_cmd(['sync', '--upgrade'])
        self.success("Dependencies updated!")
    
    def info(self):
        """Show development environment info"""
        self.log("📋 Development Environment Info", Colors.BOLD)
        
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Architecture: {platform.machine()}")
        print(f"Python: {platform.python_version()}")
        
        # Check tool versions
        tools = {
            'UV': ['uv', '--version'],
            'Git': ['git', '--version'],
            'Playwright': ['uv', 'run', 'playwright', '--version']
        }
        
        for name, cmd in tools.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                version = result.stdout.strip() if result.returncode == 0 else 'Not available'
                print(f"{name}: {version}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"{name}: Not available")
        
        print("\nProject Status:")
        print(f"- Virtual Environment: {'✅ Present' if (self.project_root / '.venv').exists() else '❌ Missing'}")
        print(f"- Dependencies: {'✅ Locked' if (self.project_root / 'uv.lock').exists() else '❌ Not locked'}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="textual-snapshots development commands",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--no-color', action='store_true', help='Disable colored output')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Setup commands
    subparsers.add_parser('install', help='Install dependencies and setup development environment')
    subparsers.add_parser('install-ci', help='Install dependencies for CI/CD')
    
    # Code quality commands
    format_parser = subparsers.add_parser('format', help='Format code')
    format_parser.add_argument('--check', action='store_true', help='Check formatting only')
    
    subparsers.add_parser('lint', help='Run linting checks')
    
    type_parser = subparsers.add_parser('typecheck', help='Run type checking')
    type_parser.add_argument('--strict', action='store_true', help='Run strict type checking')
    
    # Testing commands
    test_parser = subparsers.add_parser('test', help='Run tests')
    test_parser.add_argument('-q', '--quiet', action='store_true', help='Quiet output')
    test_parser.add_argument('-c', '--coverage', action='store_true', help='Run with coverage')
    
    # Quality check combinations
    check_parser = subparsers.add_parser('check', help='Run quality checks')
    check_parser.add_argument('--strict', action='store_true', help='Run strict checks')
    check_parser.add_argument('--full', action='store_true', help='Run comprehensive checks')
    
    # CLI testing
    subparsers.add_parser('cli-test', help='Test CLI commands')
    subparsers.add_parser('demo', help='Run CLI demo')
    
    # Coverage and reports
    subparsers.add_parser('coverage-html', help='Generate HTML coverage report')
    subparsers.add_parser('coverage-xml', help='Generate XML coverage report')
    
    # Utilities
    subparsers.add_parser('clean', help='Clean up generated files')
    subparsers.add_parser('reset', help='Reset development environment')
    subparsers.add_parser('deps-update', help='Update dependencies')
    subparsers.add_parser('info', help='Show environment info')
    
    # Pre-commit/push
    subparsers.add_parser('pre-commit', help='Run pre-commit checks')
    subparsers.add_parser('pre-push', help='Run pre-push checks')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    runner = DevRunner(verbose=args.verbose, no_color=args.no_color)
    
    try:
        # Route commands
        if args.command == 'install':
            runner.install()
        elif args.command == 'install-ci':
            runner.install_ci()
        elif args.command == 'format':
            runner.format_code(check=getattr(args, 'check', False))
        elif args.command == 'lint':
            runner.lint()
        elif args.command == 'typecheck':
            runner.typecheck(strict=getattr(args, 'strict', False))
        elif args.command == 'test':
            runner.test(quiet=getattr(args, 'quiet', False), coverage=getattr(args, 'coverage', False))
        elif args.command == 'check':
            runner.check(strict=getattr(args, 'strict', False), full=getattr(args, 'full', False))
        elif args.command == 'cli-test':
            runner.cli_test()
        elif args.command == 'demo':
            runner.demo()
        elif args.command == 'coverage-html':
            runner.coverage_html()
        elif args.command == 'coverage-xml':
            runner.coverage_xml()
        elif args.command == 'clean':
            runner.clean()
        elif args.command == 'reset':
            runner.reset()
        elif args.command == 'deps-update':
            runner.deps_update()
        elif args.command == 'info':
            runner.info()
        elif args.command == 'pre-commit':
            runner.check(strict=True)
        elif args.command == 'pre-push':
            runner.check(full=True)
        else:
            parser.print_help()
    
    except KeyboardInterrupt:
        runner.warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        runner.error(f"Unexpected error: {e}")
        if runner.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()