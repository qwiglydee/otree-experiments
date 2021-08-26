/** Timers utilities
 * Utils to use async wait and delay calls.
 * All time calues are specified in ms.
 */

class Timers {
    constructor() {
        this.timers={};
    }

    async sleep(time) {
        /** async sleep
          * Example:
          *   await timers.sleep(100); // wait for 100ms and continue code
          */
        return new Promise((resolve, reject) => {
            setTimeout(() => resolve(), time);
        });
    }

    delay(time, fn, name) {
        /** Schedule a function to call after specified time, and give it a name
          * Example:
          *   timers.delay(100, () => hideStimulus(), "hiding_stimulus"); // schedule to execute something after 100ms
          */
        this.cancel(name);
        this.timers[name] = setTimeout(() => {
            fn();
            delete this.timers[name];
        }, time);
    }

    cancel(name) {
        /** Cancel previously scheduled call
         * Example:
         *   timers.cancel('hiding_stimulus');
         */
        if (!(name in this.timers)) return;
        clearTimeout(this.timers[name]);
        delete this.timers[name];
    }

    clear() {
        /** Cancel all scheduled calls */
        for(let name in this.timers) {
            this.cancel(name);
        }
    }
}

const timers = new Timers();
