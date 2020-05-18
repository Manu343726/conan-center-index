from conans import ConanFile, tools, CMake
from conans.tools import Version
from conans.errors import ConanInvalidConfiguration
import os, re

class Enoki(ConanFile):
    name = 'enoki'
    description = 'Structured vectorization and differentiation on modern processor architectures'
    url = 'https://github.com/conan-io/conan-center-index'
    homepage = 'https://github.com/mitsuba-renderer/enoki'
    license = 'BSD-3-Clause'
    topics = 'conan', 'c++', 'simd'

    settings = 'compiler', 'os', 'arch', 'build_type'

    options = {
        'CUDA': [False],
        'AUTODIFF': [False],
        'PYTHON': [True, False],

    }
    default_options = {
        'CUDA': False,
        'AUTODIFF': False,
        'PYTHON': False,
    }

    no_copy_source = True
    _source_subfolder = 'source_subfolder'

    def configure(self):
        if self.settings.compiler.get_safe("cppstd"):
            tools.check_min_cppstd(self, '17')

        if self.settings.compiler == "gcc" and Version(self.settings.compiler.version) < "8.2":
            raise ConanInvalidConfiguration("Need gcc >= 8.2")

        if self.settings.compiler == "clang" and Version(self.settings.compiler.version) < "7.0":
            raise ConanInvalidConfiguration("Need clang >= 7.0")

        if self.settings.compiler == "Visual Studio" and Version(self.settings.compiler.version) < "15.8":
            raise ConanInvalidConfiguration("Need Visual Studio >= 2017 15.8 (MSVC 19.15)")

    def source(self):
        git = tools.Git(self._source_subfolder)
        git.clone('https://github.com/mitsuba-renderer/enoki')
        git.checkout(self.version)

        with open(os.path.join(self._source_subfolder, 'CMakeLists.txt'), 'a') as cmakelists:
            cmakelists.write('''
                set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}}" CACHE INTERNAL "")
                set(CMAKE_EXE_LINKER_FLAGS "${{CMAKE_EXE_LINKER_FLAGS}}" CACHE INTERNAL "")
                set(CMAKE_SHARED_LINKER_FLAGS "${{CMAKE_SHARED_LINKER_FLAGS}}" CACHE INTERNAL "")

                get_property(enoki_user_compile_options DIRECTORY "{dir}" PROPERTY COMPILE_OPTIONS)
                string(REPLACE ";" " " enoki_user_compile_options "${{enoki_user_compile_options}}")
                set(ENOKI_USER_CXX_FLAGS "${{enoki_user_compile_options}}" CACHE INTERNAL "")
            '''.format(dir=os.path.join(self.source_folder, self._source_subfolder)))

    def _parse_cmake_properties(self, properties):
        result = {}

        with open(os.path.join(self.build_folder, 'CMakeCache.txt'), 'r') as cmakecache:
            regex = re.compile(r'(([A-Z]|_)+)\:([A-Z]+)=(.*)\n')
            exclude_flags = [
                re.compile(r''),
                re.compile(r'\-std=(.+)'),
                re.compile(r'\/std:(.+)')
            ]

            for match in [regex.fullmatch(line) for line in cmakecache]:
                if match is not None:
                    property_name = match.group(1)
                    value = match.group(4)

                    self.output.info('{} = {}'.format(property_name, value))

                    if property_name in properties:
                        flags = []

                        for flag in value.split(' '):
                            excluded = any([r.fullmatch(flag) is not None for r in exclude_flags])

                            if not excluded:
                                flags.append(flag)

                        result[property_name] = flags

        return result

    def build(self):
        cmake = CMake(self)
        cmake.configure(
            defs = {
                'ENOKI_CUDA': self.options.CUDA,
                'ENOKI_AUTODIFF': self.options.AUTODIFF,
                'ENOKI_PYTHON': self.options.PYTHON,
                'ENOKI_TEST': False
            },
            source_folder = self._source_subfolder)

        cmake.build()

        self._flags = self._parse_cmake_properties([
            'CMAKE_CXX_FLAGS',
            'CMAKE_EXE_LINKER_FLAGS',
            'CMAKE_SHARED_LINKER_FLAGS',
            'ENOKI_USER_CXX_FLAGS'])

        self.output.info(self._flags)

    def package(self):
        self.copy("*LICENSE", dst="licenses", keep_path=False)
        self.copy("include/*", src=self._source_subfolder)
        self.copy("*.a", dst='lib/')
        self.copy("*.lib", dst='lib/')
        self.copy("*.so", dst='lib/')
        self.copy("*.dll", dst='lib/')
        self.copy("*.dylib", dst='lib/')

    def package_info(self):
        self.cpp_info.cxxflags = self._flags['CMAKE_CXX_FLAGS'] + self._flags['ENOKI_USER_CXX_FLAGS']
        self.cpp_info.exelinkflags = self._flags['CMAKE_EXE_LINKER_FLAGS']
        self.cpp_info.sharedlinkflags = self._flags['CMAKE_SHARED_LINKER_FLAGS']
