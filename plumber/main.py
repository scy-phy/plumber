import argparse
import sys
import os
import shutil
import subprocess

from typing import Final

from gts.gts_parser import GTSParser
from gts.codegen import CodeGeneratorARMA64, CodegenOffsetException
from gts.ast_state import ExpansionState

from utils.utils import format_str
from classification.measurement_utils import read_measurement_method

if __name__ == "__main__":

	# ============ PREPROCESSOR ===========

	# Read GTS string and other settings from command line args
	argparser = argparse.ArgumentParser(
		description="Transforms a Generative Testcase Specification (GTS)" + \
		" into assembly code."
	)
	
	argparser.add_argument(
		"-d", "--deterministic", nargs='?', const="state.json", metavar="STATE_JSON_FILE",
		help="Keeps the mappings from placeholders (such as 's1' for sets)" + \
		" to actual addresses across experiments instead of re-randomizing it." + \
		" The mappings will be stored in the specified json file and can later" + \
		" be reused for other GTSes. If the filename is omitted, it defaults to" + \
		" state.json."
	)
	argparser.set_defaults(deterministic=False)
	
	argparser.add_argument(
		"-v", "--verbose", action="store_true",
		help="Enables more detailed output"
	)
	argparser.set_defaults(verbose=False)

	argparser.add_argument(
		"-o", "--outdir",
		help="Output directory to store the generated code files in." + \
		" If this parameter is not provided, the generated code is written to stdout."
	)

	argparser.add_argument(
		"gts", type=str,
		help="String representation of a Generative Testcase Specification"
	)
	args = argparser.parse_args()
	
	# parse GTS string and build AST
	parser = GTSParser()
	parser.input(args.gts)
	gts = parser.parse()
	
	# print AST
	if args.verbose:
		print("====== AST =====")
		print(gts.to_str())
	
	# expand GTS: resolve all operators until the GTS only consists of sets
	# of directives
	generator = CodeGeneratorARMA64()
	expanded = gts.expand(ExpansionState(generator))
	
	# print expanded GTS
	if args.verbose:
		print("====== Expanded GTS: (precondition, main expression) =====")
		print(format_str(str(expanded)))
	
	# ============ TESTCASE INSTANTIATOR ===========

	# retry loop: sets, tags, etc. are chosen randomly during code
	# generation. If their placeholders are combined with an arithmetic
	# expression in the GTS, the resulting set/tag index may be out of
	# bounds or collide with another placeholder. In this case, retry a few
	# times and hope that we randomly choose values that fall within the
	# allowed ranges.
	retry: int = 3
	while retry > 0:
		try:
			codes = gts.codegen(generator, args.deterministic)
			retry = 0
		except CodegenOffsetException as ex:
			if retry > 1:
				print(f"Error during code generation: {ex}; retry = {retry}")
				generator.reset()
			else:
				print(f"Code generation failed. {ex} Check your arithmetic expressions.")
				sys.exit(1)
			retry -= 1

	# create outdir if it does not exist
	print(args.outdir)
	if args.outdir:
		if not os.path.exists(args.outdir):
			os.makedirs(args.outdir)
		with open(os.path.join(args.outdir, "gts.txt"), "w") as gts_file:
			gts_file.write(args.gts)
	
	if args.verbose or (not args.outdir):
		print("===== Code Generation =====")
	
	for i, (code_setup, code_main, registers_json) in enumerate(codes):
		if args.outdir:
			codedir: str = os.path.join(args.outdir, f"{i:08d}")
			os.makedirs(codedir)
			with open(os.path.join(codedir, "asm_setup.h"), "w") as code_setup_file:
				code_setup_file.write(code_setup)
			with open(os.path.join(codedir, "asm.h"), "w") as code_main_file:
				code_main_file.write(code_main)
			with open(os.path.join(codedir, "registers.json"), "w") as registers_json_file:
				registers_json_file.write(registers_json)
		if args.verbose or (not args.outdir):
			print("==== SETUP ====")
			print(code_setup)

			print("==== MAIN ====")
			print(code_main)

			print("==== REGISTERS ====")
			print(registers_json)

	# ============ Trigger the TESTCASE RUNNER ===========

	if not args.outdir:
		sys.exit(0)

	print("running executor")

	PATH_EXECUTOR_MAKEDIR: Final[str] = "../executor"
	PATH_EXECUTOR_MAKEFILE_CONFIG: Final[str] = os.path.join(PATH_EXECUTOR_MAKEDIR, "Makefile.config")
	PATH_EXECUTOR_CODEDIR: Final[str] = "../executor/code"
	PATH_EXECUTOR_LOGFILE: Final[str] = "../executor/uart.log"

	# Parse Makefile.config to find the measurement method
	measurement_method: str = read_measurement_method(PATH_EXECUTOR_MAKEFILE_CONFIG)

	# Run experiments, one after another
	for experiment_dir in sorted(os.listdir(args.outdir)):
		experiment_dir = os.path.join(args.outdir, experiment_dir)
		if not os.path.isdir(experiment_dir):
			continue
		print(f"running experiment {experiment_dir}...")
		
		# copy code files into executor directory
		shutil.copy(
			os.path.join(experiment_dir, "asm.h"),
			os.path.join(PATH_EXECUTOR_CODEDIR, "asm.h")
		)
		shutil.copy(
			os.path.join(experiment_dir, "asm_setup.h"),
			os.path.join(PATH_EXECUTOR_CODEDIR, "asm_setup.h")
		)

		# run the executor
		executor_process = subprocess.Popen(["make", "-C", PATH_EXECUTOR_MAKEDIR, "clean", "runlog"])
		executor_process.wait()
		if executor_process.returncode != 0:
			raise Exception(f"Executor process failed with returncode {executor_process.returncode}.")
		
		# copy measurement log (uart.log) into experiment folder
		path_measurement_logfile: str = os.path.join(experiment_dir, f"uart.log")
		shutil.copy(PATH_EXECUTOR_LOGFILE, path_measurement_logfile)

