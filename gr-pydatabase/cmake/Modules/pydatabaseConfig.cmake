INCLUDE(FindPkgConfig)
PKG_CHECK_MODULES(PC_PYDATABASE pydatabase)

FIND_PATH(
    PYDATABASE_INCLUDE_DIRS
    NAMES pydatabase/api.h
    HINTS $ENV{PYDATABASE_DIR}/include
        ${PC_PYDATABASE_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    PYDATABASE_LIBRARIES
    NAMES gnuradio-pydatabase
    HINTS $ENV{PYDATABASE_DIR}/lib
        ${PC_PYDATABASE_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/pydatabaseTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(PYDATABASE DEFAULT_MSG PYDATABASE_LIBRARIES PYDATABASE_INCLUDE_DIRS)
MARK_AS_ADVANCED(PYDATABASE_LIBRARIES PYDATABASE_INCLUDE_DIRS)
