#!/usr/bin/env python
import json
import logging
import click
from blessed import Terminal
from wardriver import WardriverManager

logger = logging.getLogger(__name__)
term = Terminal()

@click.group(help="Wardriver CLI")
def cli():
    pass

@cli.command(name="load")
@click.option("--config-file", type=click.Path(exists=True), help="Path to the configuration file", required=True)
def load(config_file):
    """Load radio modules from a configuration file."""
    with open(config_file, 'r') as file:
        configs = json.load(file)
    
    manager = WardriverManager()
    manager.load_radio_modules(configs)
    click.echo(f"Loaded {len(manager.radio_modules)} radio modules.")

@cli.command(name="configure")
@click.option("--identifier", required=True, help="Identifier of the radio module to configure")
@click.option("--mode", required=True, type=click.Choice(['fuzzing', 'jamming']), help="Mode to set")
@click.option("--attack-type", required=True, type=click.Choice(['targeted', 'selected', 'indiscriminate']), help="Type of attack")
@click.option("--target", required=False, help="Target for the attack (optional)")
def configure(identifier, mode, attack_type, target):
    """Configure a radio module."""
    manager = WardriverManager()
    manager.configure_module(identifier, mode, attack_type, target)
    click.echo(f"Configured module {identifier} with mode {mode} and attack type {attack_type}.")

@cli.command(name="run")
def run():
    """Run all configured radio modules."""
    manager = WardriverManager()
    manager.run_modules()
    click.echo("Running all radio modules.")

@cli.command(name="scan")
def scan():
    """Scan for radio modules."""
    manager = WardriverManager()
    modules = manager.scan_drivers()
    click.echo(f"Found {len(modules)} radio modules.")
    for module in modules:
        click.echo(f"Module: {module.identifier}")

@cli.command(name="interactive")
def interactive():
    """Start interactive CLI."""
    manager = WardriverManager()

    def draw_menu():
        print(term.clear)
        print(term.bold("Wardriver Interactive CLI"))
        print(term.bold("-" * 30))
        print("1. Load radio modules")
        print("2. Configure a module")
        print("3. Run all modules")
        print("4. Scan for modules")
        print("5. Exit")
        print(term.bold("-" * 30))

    while True:
        draw_menu()
        choice = input(term.bold("Enter choice: "))

        if choice == '1':
            config_file = input("Enter the path to the configuration file: ")
            with open(config_file, 'r') as file:
                configs = json.load(file)
            manager.load_radio_modules(configs)
            print(f"Loaded {len(manager.radio_modules)} radio modules.")
        elif choice == '2':
            identifier = input("Enter the identifier of the radio module: ")
            mode = input("Enter mode (fuzzing/jamming): ")
            attack_type = input("Enter attack type (targeted/selected/indiscriminate): ")
            target = input("Enter target (optional): ") or None
            manager.configure_module(identifier, mode, attack_type, target)
            print(f"Configured module {identifier} with mode {mode} and attack type {attack_type}.")
        elif choice == '3':
            manager.run_modules()
            print("Running all radio modules.")
        elif choice == '4':
            modules = manager.scan_drivers()
            print(f"Found {len(modules)} radio modules.")
            for module in modules:
                print(f"Module: {module.identifier}")
        elif choice == '5':
            print("Exiting...")
            break
        else:
            print("Invalid choice, please try again.")

def main():
    cli()

if __name__ == "__main__":
    main()
