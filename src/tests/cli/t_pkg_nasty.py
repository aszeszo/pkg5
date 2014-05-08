#!/usr/bin/python
#
# CDDL HEADER START
#
# The contents of this file are subject to the terms of the
# Common Development and Distribution License (the "License").
# You may not use this file except in compliance with the License.
#
# You can obtain a copy of the license at usr/src/OPENSOLARIS.LICENSE
# or http://www.opensolaris.org/os/licensing.
# See the License for the specific language governing permissions
# and limitations under the License.
#
# When distributing Covered Code, include this CDDL HEADER in each
# file and include the License file at usr/src/OPENSOLARIS.LICENSE.
# If applicable, add the following below this CDDL HEADER, with the
# fields enclosed by brackets "[]" replaced with your own identifying
# information: Portions Copyright [yyyy] [name of copyright owner]
#
# CDDL HEADER END
#

#
# Copyright (c) 2012, 2014 Oracle and/or its affiliates. All rights reserved.
#

import testutils
if __name__ == "__main__":
        testutils.setup_environment("../../../proto")
import pkg5unittest

import os
import unittest
import signal
import time

import pkg.portable as portable

class TestNastySig(pkg5unittest.SingleDepotTestCase):
        # Only start/stop the depot once (instead of for every test)
        persistent_setup = True

        foo10 = """
            open foo@1.0,5.11-0
            close """

        def setUp(self):
                pkg5unittest.SingleDepotTestCase.setUp(self)
                self.pkgsend_bulk(self.rurl, self.foo10)

        def test_00_sig(self):
                """Verify pkg client handles SIGTERM, SIGHUP, SIGINT gracefully
                and writes a history entry if possible."""

                if portable.osname == "windows":
                        # SIGHUP not supported on Windows.
                        sigs = (signal.SIGINT, signal.SIGTERM)
                else:
                        sigs = (signal.SIGHUP, signal.SIGINT, signal.SIGTERM)

                for sig in sigs:
                        self.pkg_image_create(self.rurl)

                        imgdir = os.path.join(self.img_path(), "var", "pkg")
                        self.assert_(os.path.exists(imgdir))

                        hfile = os.path.join(imgdir, "pkg5.hang")
                        self.assert_(not os.path.exists(hfile))

                        self.pkg("purge-history")

                        hndl = self.pkg(
                            ["-D", "simulate-plan-hang=true", "install", "foo"],
                            handle=True, coverage=False)

                        # Wait for hang file before sending signal.
                        while not os.path.exists(hfile):
                                self.assertEqual(hndl.poll(), None)
                                time.sleep(0.25)

                        hndl.send_signal(sig)
                        rc = hndl.wait()

                        self.assertEqual(rc, 1)

                        # Verify that history records operation as canceled.
                        self.pkg(["history", "-H"])
                        hentry = self.output.splitlines()[-1]
                        self.assert_("install" in hentry)
                        self.assert_("Canceled" in hentry)


if __name__ == "__main__":
        unittest.main()
